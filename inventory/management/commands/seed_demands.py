from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from inventory.models import Trade, Instructor, Item, DemandNote, DemandItem, FINANCIAL_YEAR_CHOICES, ItemGroup
import random
from datetime import datetime, timedelta

class Command(BaseCommand):
    help = 'Seeds dummy data for instructors and demands'

    def handle(self, *args, **kwargs):
        # 1. Groups
        g_stor, _ = Group.objects.get_or_create(name='StoreKeepers')
        g_inst, _ = Group.objects.get_or_create(name='Instructors')

        # 2. Trades
        trades_list = [
            ('Electrician', 4),
            ('Fitter', 4),
            ('ICTSM', 4),
            ('Wireman', 4),
            ('Welder', 2),
        ]
        trade_objs = []
        for name, sems in trades_list:
            t, _ = Trade.objects.get_or_create(trade_name=name, defaults={'total_semesters': sems})
            trade_objs.append(t)

        # 3. Item Groups & Items if missing
        if Item.objects.count() < 5:
            ig, _ = ItemGroup.objects.get_or_create(name='General')
            Item.objects.get_or_create(item_code='ST-001', defaults={'item_name': 'A4 Paper', 'item_unit': 'Ream', 'est_price': 250, 'group': ig})
            Item.objects.get_or_create(item_code='ST-002', defaults={'item_name': 'Blue Pen', 'item_unit': 'Nos', 'est_price': 10, 'group': ig})
            Item.objects.get_or_create(item_code='ST-003', defaults={'item_name': 'Pencil', 'item_unit': 'Nos', 'est_price': 5, 'group': ig})

        all_items = list(Item.objects.all())
        fy_list = [f[0] for f in FINANCIAL_YEAR_CHOICES]

        # 4. Instructors
        instructors_data = [
            ('vinod_elec', 'Vinod Sawant', 'Electrician'),
            ('amit_fitter', 'Amit Sharma', 'Fitter'),
            ('sunita_ictsm', 'Sunita Patil', 'ICTSM'),
        ]

        for uname, fname, tname in instructors_data:
            user, created = User.objects.get_or_create(username=uname)
            if created:
                user.set_password('Test@1234')
                user.save()
            user.groups.add(g_inst)
            
            trade = Trade.objects.get(trade_name=tname)
            instructor, _ = Instructor.objects.get_or_create(user=user, defaults={'name': fname, 'trade': trade})

            # Create mixed demands
            for status in ['DRAFT', 'SUBMITTED', 'MERGED']:
                dn = DemandNote.objects.create(
                    instructor=instructor,
                    trade=trade,
                    semester_no=random.randint(1, 4),
                    financial_year=random.choice(fy_list),
                    status=status,
                    remarks=f"Sample {status} demand by {fname}",
                    created_at=datetime.now() - timedelta(days=random.randint(1, 40))
                )
                
                if status != 'DRAFT':
                    dn.submitted_at = dn.created_at + timedelta(hours=status=='MERGED' and 24 or 2)
                    dn.save()

                # Add dummy items
                note_items = random.sample(all_items, k=min(len(all_items), random.randint(2, 4)))
                for item in note_items:
                    DemandItem.objects.create(
                        demand_note=dn,
                        item=item,
                        quantity_required=random.randint(1, 100)
                    )

        self.stdout.write(self.style.SUCCESS("Demo data seeded! Check 'All Demands' as StoreKeeper or login as instructors (Vinod, Amit, Sunita). Password: Test@1234"))
