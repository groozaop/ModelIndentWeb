from django.urls import path
from . import views

app_name = 'inventory'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),

    # API
    path('api/items/', views.item_data_json, name='item_data_json'),

    # Registration
    path('register/', views.register_instructor, name='register'),

    # Instructor: Demand Note CRUD
    path('demand/create/', views.create_demand, name='create_demand'),
    path('demand/<int:demand_id>/', views.view_demand, name='view_demand'),
    path('demand/<int:demand_id>/edit/', views.edit_demand, name='edit_demand'),
    path('demand/<int:demand_id>/submit/', views.submit_demand, name='submit_demand'),
    path('demand/<int:demand_id>/delete/', views.delete_demand, name='delete_demand'),
    path('demands/', views.my_demands, name='my_demands'),

    # StoreKeeper: Demand management
    path('store/demands/', views.all_demands, name='all_demands'),
    path('store/demand/<int:demand_id>/', views.store_view_demand, name='store_view_demand'),

    # StoreKeeper: Merge & Ultimate Query
    path('merge/', views.merge_demand, name='merge_demand'),
    path('merge/mark/', views.mark_merged, name='mark_merged'),
    path('queries/', views.ultimate_query_list, name='ultimate_query_list'),
    path('query/<int:uq_id>/', views.ultimate_query_detail, name='ultimate_query_detail'),
    path('query-export/<int:uq_id>/', views.export_ultimate_query_xls, name='export_ultimate_query_xls'),

    # GPR
    path('gpr/add/', views.add_gpr, name='add_gpr'),
    path('gpr/', views.gpr_list, name='gpr_list'),

    # CR
    path('gpr/<int:gpr_id>/allocate/', views.allocate_cr, name='allocate_cr'),
    path('cr/', views.cr_list, name='cr_list'),
]
