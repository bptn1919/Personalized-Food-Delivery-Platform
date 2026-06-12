"""
Production-grade Dish Search Service
Pipeline: Normalize → Retrieve (Fuzzy + Alias) → Semantic → Rank → Filter
"""

from typing import Optional, List, Set
from uuid import UUID
from difflib import SequenceMatcher
from django.db.models import Q, Value, F, FloatField, ExpressionWrapper, Case, When
from django.db.models.functions import Greatest
from utils.functions.remove_accents import remove_accents
from dish.models import Dish, DishAlias, DishAvailability, DishIngredient
from profile.models import CustomerFavoriteDish, CustomerProfile
from ingredient.models import AllergicIngredient
from utils.enums import DishCategoryEnum, DishStatusEnum, AllergyModeEnum
from utils.types import TUser
from django.utils import timezone
from datetime import date


class DishSearchService:
    """
    Search service với đầy đủ production features:
    - Normalize: xóa accent, lowercase, trim
    - Retrieve: fuzzy match name + alias mapping
    - Semantic: TF-IDF-like scoring
    - Rank: theo độ chính xác, rating, popularity
    - Filter: theo category, location, status, availability
    """
    
    # Fuzzy matching threshold (0-1)
    FUZZY_THRESHOLD = 0.1
    
    # Weights cho ranking
    RANK_WEIGHTS = {
        'exact_name_match': 1.0,      # Khớp chính xác tên
        'exact_alias_match': 0.95,    # Khớp chính xác alias
        'fuzzy_name_match': 0.8,      # Fuzzy match tên
        'fuzzy_alias_match': 0.75,    # Fuzzy match alias
        'rating_boost': 0.2,          # Điểm rating
        'popularity_boost': 0.15,     # Độ phổ biến (số lần order)
    }
    
    @staticmethod
    def normalize(text: str) -> str:
        """Normalize query text: remove accent, lowercase, strip"""
        if not text:
            return ""
        return remove_accents(text).lower().strip()
    
    @classmethod
    def _calculate_fuzzy_score(cls, query: str, target: str) -> float:
        """
        Tính fuzzy matching score (0-1)
        Sử dụng SequenceMatcher từ difflib
        """
        query_norm = query
        target_norm = cls.normalize(target)
        
        if query_norm == target_norm:
            return 1.0
        
        ratio = SequenceMatcher(None, query_norm, target_norm).ratio()
        return max(0.0, ratio)
    
    @classmethod
    def retrieve_candidates(cls, query: str) -> List[tuple[Dish, float, str]]:
        """
        Retrieve candidates từ DB theo query
        Return: List[(Dish, score, match_type)]
        Match types: 'exact_name', 'exact_alias', 'fuzzy_name', 'fuzzy_alias'
        """
        query_norm = query
        candidates = {}  # {dish_id: (Dish, max_score, match_type)}
        
        if not query_norm:
            return []
        
        # 1. Exact match trên tên chính (name_no_accent)
        exact_name_dishes = Dish.objects.filter(
            name_no_accent__iexact=query_norm,
            deleted=False
        ).select_related('attachment')
        
        for dish in exact_name_dishes:
            candidates[dish.uid] = (dish, 1.0, 'exact_name')
        
        # 2. Exact match trên aliases
        exact_alias_dishes = DishAlias.objects.filter(
            alias_name_no_accent__iexact=query_norm
        ).select_related('dish', 'dish__attachment')
        for alias in exact_alias_dishes:
            dish = alias.dish
            if dish.uid not in candidates:
                candidates[dish.uid] = (dish, 0.98, 'exact_alias')
            elif candidates[dish.uid][1] < 0.98:
                candidates[dish.uid] = (dish, 0.98, 'exact_alias')
        
        # 3. Fuzzy match trên tên chính
        all_dishes = Dish.objects.filter(
            deleted=False
        ).select_related('attachment')
        
        for dish in all_dishes:
            if dish.uid in candidates:
                continue  # Skip nếu đã có exact match
            score = cls._calculate_fuzzy_score(query_norm, dish.name_no_accent)
            # if score >= cls.FUZZY_THRESHOLD:
            candidates[dish.uid] = (dish, score, 'fuzzy_name')
        # 4. Fuzzy match trên aliases
        fuzzy_aliases = DishAlias.objects.filter(
            dish__deleted=False
        ).select_related('dish', 'dish__attachment')
        
        for alias in fuzzy_aliases:
            if alias.dish.uid in candidates:
                continue  # Skip nếu đã có score cao hơn
            
            score = cls._calculate_fuzzy_score(query_norm, alias.alias_name_no_accent)
            # if score >= cls.FUZZY_THRESHOLD:
            if alias.dish.uid not in candidates or candidates[alias.dish.uid][1] < score:
                candidates[alias.dish.uid] = (alias.dish, score, 'fuzzy_alias')
        
        return list(candidates.values())
    
    @classmethod
    def semantic_rank(
        cls,
        candidates: List[tuple[Dish, float, str]],
        query: str
    ) -> List[tuple[Dish, float]]:
        """
        Semantic ranking: tính score dựa trên:
        - Độ chính xác fuzzy
        - Rating trung bình
        - Độ phổ biến
        """
        ranked = []
        
        for dish, fuzzy_score, match_type in candidates:
            # Base score từ fuzzy matching
            if match_type == 'exact_name':
                base_score = cls.RANK_WEIGHTS['exact_name_match']
            elif match_type == 'exact_alias':
                base_score = cls.RANK_WEIGHTS['exact_alias_match']
            elif match_type == 'fuzzy_name':
                base_score = cls.RANK_WEIGHTS['fuzzy_name_match'] * fuzzy_score
            else:  # fuzzy_alias
                base_score = cls.RANK_WEIGHTS['fuzzy_alias_match'] * fuzzy_score
            
            # Boost từ rating (0-5 -> 0-0.2)
            rating_boost = min(
                cls.RANK_WEIGHTS['rating_boost'],
                (dish.avg_rating / 5.0) * cls.RANK_WEIGHTS['rating_boost']
            ) if dish.avg_rating else 0
            
            # Boost từ final_score (popularity)
            popularity_boost = min(
                cls.RANK_WEIGHTS['popularity_boost'],
                (dish.final_score / 100.0) * cls.RANK_WEIGHTS['popularity_boost']
            ) if dish.final_score else 0
            
            final_score = base_score + rating_boost + popularity_boost
            ranked.append((dish, final_score))
        
        # Sort by score desc
        ranked.sort(key=lambda x: x[1], reverse=True)
        return ranked
    
    @classmethod
    def filter_results(
        cls,
        dishes: List[tuple[Dish, float]],
        category: Optional[str] = None,
        location_id: Optional[int] = None,
        status: Optional[str] = None,
        available_today: bool = False,
        limit: int = 50,
        favorite_ids: Optional[Set[UUID]] = None,
    ) -> List[dict]:
        """
        Filter và format kết quả
        """
        favorite_ids = favorite_ids or set()
        filtered = []
        
        for dish, score in dishes:
            # Filter by category
            if category and dish.category != category:
                continue
            
            # Filter by location
            if location_id:
                if not dish.location_id:
                    continue
                # Check location hierarchy
                location_match = (
                    dish.location_id == location_id
                    or (dish.location and dish.location.parent_id == location_id)
                    or (dish.location and dish.location.parent and dish.location.parent.parent_id == location_id)
                )
                if not location_match:
                    continue
            
            # Filter by status
            if status and dish.status != status:
                continue
            
            # Filter by availability today
            if available_today:
                today = date.today()
                available = DishAvailability.objects.filter(
                    dish=dish,
                    available_date=today,
                    is_available=True
                ).exists()
                if not available:
                    continue
            
            filtered.append({
                'uid': str(dish.uid),
                'name': dish.name,
                'category': dish.category,
                'price': float(dish.price),
                'description': dish.description,
                'status': dish.status,
                'rating': float(dish.avg_rating) if dish.avg_rating else 0,
                'popularity_score': float(dish.final_score) if dish.final_score else 0,
                'search_score': round(float(score), 4),  # Điểm search (0-2)
                'image_url': dish.attachment.public_url if dish.attachment else None,
                'location_id': dish.location_id,
                'is_favorite': dish.uid in favorite_ids,
            })
        
        return filtered[:limit]
    
    @classmethod
    def search(
        cls,
        query: str,
        user: TUser | None = None,
        category: Optional[str] = None,
        location_id: Optional[int] = None,
        status: Optional[str] = None,
        available_today: bool = False,
        limit: int = 50,
    ) -> dict:
        """
        Main search pipeline
        
        Args:
            query: search query string
            category: filter by DishCategoryEnum (optional)
            location_id: filter by location (optional)
            status: filter by status (optional)
            available_today: chỉ lấy món có sẵn hôm nay (optional)
            limit: giới hạn kết quả (default 50)
        
        Returns:
            dict với keys:
            - query: query đã normalize
            - total: số kết quả
            - results: list dict của các dish với scores
        """
        # Step 1: Normalize
        query_norm = cls.normalize(query)
        
        if not query_norm:
            return {
                'query': query_norm,
                'total': 0,
                'results': [],
                'message': 'Empty query'
            }
        
        # Step 2: Retrieve candidates
        candidates = cls.retrieve_candidates(query_norm)

        # Step 3: Semantic ranking
        ranked = cls.semantic_rank(candidates, query_norm)

        favorite_ids: Set[UUID] = set()
        allergy_mode = AllergyModeEnum.WARN
        allergic_ids: List[UUID] = []

        if user:
            profile = CustomerProfile.objects.filter(user_id=user.id).first()
            if profile:
                allergy_mode = profile.allergy_mode

            allergic_ids = list(
                AllergicIngredient.objects.filter(
                    user_id=user.id,
                    deleted=False
                ).values_list("ingredient_id", flat=True)
            )

            favorite_ids = set(
                CustomerFavoriteDish.objects.filter(
                    user_id=user.id,
                    deleted=False
                ).values_list("dish_id", flat=True)
            )

        # Hide dishes containing allergic ingredients when mode is HIDE
        if user and allergy_mode == AllergyModeEnum.HIDE and allergic_ids and ranked:
            ranked_ids = [dish.uid for dish, _ in ranked]
            allergic_dish_ids = set(
                DishIngredient.objects.filter(
                    dish_id__in=ranked_ids,
                    ingredient_id__in=allergic_ids,
                    deleted=False
                ).values_list("dish_id", flat=True)
            )
            ranked = [
                (dish, score)
                for dish, score in ranked
                if dish.uid not in allergic_dish_ids
            ]

        # Step 4: Filter & format
        results = cls.filter_results(
            ranked,
            category=category,
            location_id=location_id,
            status=status,
            available_today=available_today,
            limit=limit,
            favorite_ids=favorite_ids,
        )
        return {
            'query': query_norm,
            'total': len(results),
            'results': results,
        }
