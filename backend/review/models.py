from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from utils.models import BaseModel
from utils.types import User


class Review(BaseModel):
    """Review của customer cho món ăn sau khi đã order"""
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Rating từ 1-5 sao"
    )
    comment = models.TextField(null=True, blank=True)
    weight = models.FloatField(default=0.0)
    issue = models.CharField(max_length=100, null=True, blank=True)
    
    dish = models.ForeignKey(
        to="dish.Dish",
        on_delete=models.CASCADE,
        to_field="uid",
        db_column="dish_uid",
        related_name="review_fk_dish",
        db_constraint=True,
        null=False,
        blank=False,
    )
    
    order = models.ForeignKey(
        to="order.Order",
        on_delete=models.SET_NULL,
        to_field="uid",
        db_column="order_uid",
        related_name="review_fk_order",
        db_constraint=True,
        null=True,
        blank=True,
        help_text="Order mà user đã mua món này"
    )
    
    owner = models.ForeignKey(
        to=User,
        on_delete=models.SET_NULL,
        to_field="id",
        db_column="owner_id",
        related_name="review_fk_owner",
        db_constraint=True,
        null=True,
        blank=True,
    )
    
    attachment = models.ForeignKey(
        to="attachment.Attachment",
        on_delete=models.SET_NULL,
        to_field="uid",
        db_column="attachment_uid",
        related_name="review_fk_attachment",
        db_constraint=True,
        null=True,
        blank=True,
        help_text="Hình ảnh đính kèm review (optional)"
    )
    
    deleted = models.BooleanField(default=False, null=False, blank=False)
    
    class Meta:
        ordering = ["-created_at"]
        # Đảm bảo mỗi user chỉ review 1 lần cho mỗi dish trong 1 order
        unique_together = [["owner", "dish", "order"]]
    
    def __str__(self) -> str:
        return f"Review by {self.owner} for {self.dish} - {self.rating}⭐"


class ReviewReply(BaseModel):
    """Reply của chef cho review của customer"""
    review = models.OneToOneField(
        to=Review,
        on_delete=models.CASCADE,
        to_field="uid",
        db_column="review_uid",
        related_name="reply",
        db_constraint=True,
        null=False,
        blank=False,
        help_text="Review được reply"
    )
    
    content = models.TextField(help_text="Nội dung reply của chef")
    
    owner = models.ForeignKey(
        to=User,
        on_delete=models.SET_NULL,
        to_field="id",
        db_column="owner_id",
        related_name="review_reply_fk_owner",
        db_constraint=True,
        null=True,
        blank=True,
        help_text="Chef reply"
    )
    
    deleted = models.BooleanField(default=False, null=False, blank=False)
    
    class Meta:
        ordering = ["-created_at"]
    
    def __str__(self) -> str:
        return f"Reply by {self.owner} to Review {self.review.uid}"
