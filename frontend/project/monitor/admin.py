#from django.contrib import admin
#from .models import Services, Systems, SystemsLogs, SystemsMetrics, ServiceAvailability, InternetAvailability


#class ServicesAdmin(admin.ModelAdmin):
#    list_display = "service_name", "service_url", "service_protocol", "service_port"
#    search_fields = "service_name", "service_url", "service_protocol", "service_port"

#class SystemsAdmin(admin.ModelAdmin):
#    list_display = "system_name", "system_os", "system_hostname", "system_IPs", "system_RAM", "system_HDD"
#    search_fields = "system_name", "system_os", "system_hostname", "system_IPs", "system_RAM", "system_HDD"

#class SystemsLogsAdmin(admin.ModelAdmin):
#    list_display = "system", "event_level", "event_id", "event_time", "description"
#    search_fields = "system", "event_level", "event_id", "event_time", "description"

#    def get_queryset(self, request):
#        return SystemsLogs.objects.select_related("system")

#class SystemsMetricsAdmin(admin.ModelAdmin):
#    list_display = "system", "uptime", "cpu_load_1", "cpu_load_5", "cpu_load_15", "ram_load", "disk_usage"
#    search_fields = "system", "uptime", "cpu_load_1", "cpu_load_5", "cpu_load_15", "ram_load", "disk_usage"

#    def get_queryset(self, request):
#        return SystemsMetrics.objects.select_related("system")

#class ServiceAvailabilityAdmin(admin.ModelAdmin):
#    list_display = "service", "check_time", "service_availability", "service_rtt"
#    search_fields = "service", "check_time", "service_availability", "service_rtt"

#    def get_queryset(self, request):
#        return ServiceAvailability.objects.select_related("service")


#class InternetAvailabilityAdmin(admin.ModelAdmin):
#    list_display = "check_time", "google_rtt", "yandex_rtt", "gateway_rtt"
#    search_fields = "check_time", "google_rtt", "yandex_rtt", "gateway_rtt"

#admin.site.register(Services, ServicesAdmin)
#admin.site.register(Systems, SystemsAdmin)
#admin.site.register(SystemsLogs, SystemsLogsAdmin)
#admin.site.register(SystemsMetrics, SystemsMetricsAdmin)
#admin.site.register(ServiceAvailability, ServiceAvailabilityAdmin)
#admin.site.register(InternetAvailability, InternetAvailabilityAdmin)
