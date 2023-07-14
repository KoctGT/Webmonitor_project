from django.db import models

class Systems(models.Model):
    system_name = models.CharField(max_length=20, unique=True) # Unique system name
    device_type = models.CharField(max_length=20) # For Netmiko
    os = models.CharField(max_length=50, null=True) # lsb_release -a \ cat /proc/version
    hostname = models.CharField(max_length=20, null=True) # hostname
    host = models.CharField(max_length=100, null=True)
    RAM = models.CharField(max_length=20, null=True) #  top
    HDD = models.CharField(max_length=20, null=True) # df -h
    username = models.CharField(max_length=20, null=True)
    password = models.CharField(max_length=128, null=True)
    key_file = models.CharField(max_length=255, null=True)
    timeout = models.IntegerField() # For Netmiko
    enabled = models.BooleanField()

class SystemsLogs(models.Model):
    system = models.ForeignKey(Systems, on_delete=models.PROTECT) # orangePIOS/Win/notebook
    priority = models.IntegerField(null=False, blank=True, default=None)
    pid = models.IntegerField(null=False, blank=True, default=None)
    realtime_timestamp = models.IntegerField(null=False, blank=True, default=None)
    message = models.TextField(null=False, blank=True, default=None)
    hostname = models.CharField(max_length=40, null=True)
    code_func = models.CharField(max_length=255, null=True)
    cmdline = models.CharField(max_length=255, null=True)
    ignored = models.BooleanField(default=False)
    solved = models.BooleanField(default=False)

class SystemsMetrics(models.Model):
    system = models.ForeignKey(Systems, on_delete=models.PROTECT)
    check_time = models.CharField(blank=True, max_length=255)
    uptime = models.CharField(max_length=20, null=True)
    cpu_load_1 = models.DecimalField(max_digits=4, decimal_places=2, null=True)
    cpu_load_5 = models.DecimalField(max_digits=4, decimal_places=2, null=True)
    cpu_load_15 = models.DecimalField(max_digits=4, decimal_places=2, null=True)
    mem_used = models.DecimalField(max_digits=6, decimal_places=2, null=True) # top
    disk_usage = models.DecimalField(max_digits=4, decimal_places=1, null=True) # df -h

class Services(models.Model):
    service_name = models.CharField(max_length=20, unique=True)
    protocol = models.CharField(max_length=20, null=True) # http \ https
    host = models.CharField(max_length=100)
    port = models.IntegerField()
    path = models.CharField(max_length=255, null=False, blank=True, default=None)
    correct_http_response_code = models.IntegerField(null=True) # 200
    correct_http_response = models.CharField(max_length=100, null=True) # http response body
    enabled = models.BooleanField()

class IServices(models.Model):
    service_name = models.CharField(max_length=20, unique=True)
    IPv4 = models.CharField(max_length=20)
    enabled = models.BooleanField()

class ServiceAvailability(models.Model):
    service = models.ForeignKey(Services, on_delete=models.PROTECT)
    check_time = models.CharField(blank=True, max_length=255)
    availability = models.BooleanField()

class InternetAvailability(models.Model):
    check_time = models.CharField(blank=True, max_length=255)
    iservice = models.ForeignKey(IServices, on_delete=models.PROTECT)
    availability = models.BooleanField()
    destination = models.CharField(max_length=20, null=True)
    packet_transmit = models.IntegerField()
    packet_receive = models.IntegerField()
    packet_loss_count = models.IntegerField()
    packet_loss_rate = models.DecimalField(max_digits=6, decimal_places=3)
    rtt_min = models.DecimalField(max_digits=6, decimal_places=3, null=True)
    rtt_avg = models.DecimalField(max_digits=6, decimal_places=3, null=True)
    rtt_max = models.DecimalField(max_digits=6, decimal_places=3, null=True)
    rtt_mdev = models.DecimalField(max_digits=6, decimal_places=3, null=True)
    packet_duplicate_count = models.IntegerField(null=True)
    packet_duplicate_rate = models.DecimalField(max_digits=6, decimal_places=3, null=True)



