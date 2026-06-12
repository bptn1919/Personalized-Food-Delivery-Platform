from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission


class Command(BaseCommand):
    help = 'Setup Groups and Permissions for RBAC (using DEFAULT Django permissions only)'

    def handle(self, *args, **kwargs):
        # Tạo hoặc lấy Groups với ID cụ thể
        customer_group, created = Group.objects.get_or_create(id=1, defaults={'name': 'CUSTOMER'})
        chef_group, created = Group.objects.get_or_create(id=2, defaults={'name': 'CHEF'})
        admin_group, created = Group.objects.get_or_create(id=3, defaults={'name': 'ADMIN'})

        # CUSTOMER - View Dish/Menu/Availability only, Add/View Checkout & Order
        # IDs từ he.json: dish(48), dishingredient(44), ingredient(52), dishavailability(40), menu(56), menudish(60), checkout(81,84), order(85,88)
        customer_perm_ids = [
            40,  # view_dishavailability (xem ngày nào dish có sẵn)
            44,  # view_dishingredient (xem thành phần món ăn)
            48,  # view_dish
            52,  # view_ingredient (xem nguyên liệu)
            56,  # view_menu
            60,  # view_menudish (xem món nào trong menu)
            64,
            65,
            66,
            67,
            68,
            69,
            70,
            71,
            72,
            76,
            77,
            78,
            79,
            80,
            81,  # add_checkout
            82,  # change_checkout
            84,  # view_checkout
            85,  # add_order
            88,  # view_order
            89,
            92,
        ]
        customer_perms = Permission.objects.filter(id__in=customer_perm_ids)
        customer_group.permissions.set(customer_perms)
        self.stdout.write(self.style.SUCCESS(f'✅ CUSTOMER (id=1): {customer_perms.count()} permissions'))

        # CHEF - Add/Change/Delete/View Dish & Availability & Menu, View/Change Orders
        # IDs từ he.json: dish(45-48), dishingredient(41-44), ingredient(49-52), dishavailability(37-40), menu(53-56), menudish(57-60), order(86,88)
        chef_perm_ids = [
            33,34,35,36,
            37,38,39,40,  # dishavailability: add, change, delete, view
            41,42,43,44,  # dishingredient: add, change, delete, view
            45,  # add_dish
            46,  # change_dish
            47,  # delete_dish
            48,  # view_dish
            49,50,51,52,  # ingredient: add, change, delete, view
            53,  # add_menu
            54,  # change_menu
            55,  # delete_menu
            56,  # view_menu
            57,  # add_menudish (thêm món vào menu)
            58,  # change_menudish
            59,  # delete_menudish
            60,  # view_menudish
            61,62,63,64, #chef profile
            86,  # change_order
            88,  # view_order
        ]
        chef_perms = Permission.objects.filter(id__in=chef_perm_ids)
        chef_group.permissions.set(chef_perms)
        self.stdout.write(self.style.SUCCESS(f'✅ CHEF (id=2): {chef_perms.count()} permissions'))

        # ADMIN - Full permissions
        admin_perm_ids = [
            45, 46, 47, 48,  # dish: add, change, delete, view
            41, 42, 43, 44,  # dishingredient: add, change, delete, view
            49, 50, 51, 52,  # ingredient: add, change, delete, view
            37, 38, 39, 40,  # dishavailability: add, change, delete, view
            53, 54, 55, 56,  # menu: add, change, delete, view
            57, 58, 59, 60,  # menudish: add, change, delete, view
            81, 82, 83, 84,  # checkout: add, change, delete, view
            85, 86, 87, 88,  # order: add, change, delete, view
        ]
        admin_perms = Permission.objects.filter(id__in=admin_perm_ids)
        admin_group.permissions.set(admin_perms)
        self.stdout.write(self.style.SUCCESS(f'✅ ADMIN (id=3): {admin_perms.count()} permissions'))

        self.stdout.write(self.style.SUCCESS('\n🎉 Groups và permissions đã được cấu hình'))
        
        # Hiển thị chi tiết
        self.stdout.write('\n📋 Chi tiết permissions:')
        for group in [customer_group, chef_group, admin_group]:
            self.stdout.write(f'\n{group.name} (id={group.id}):')
            for perm in group.permissions.all().order_by('id'):
                self.stdout.write(f'  - [{perm.id}] {perm.codename}')
