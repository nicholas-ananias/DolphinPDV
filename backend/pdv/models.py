from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin

class UserManager(BaseUserManager):
    def create_user(self, username, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The email is required')
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None, **extra_fields):
        extra_fields.setdefault('is_admin', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(username, email, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    name = models.CharField(max_length=100)
    username = models.CharField(max_length=100, unique=True)
    email = models.EmailField(max_length=100, unique=True)
    profile_picture = models.CharField(max_length=200, blank=True, null=True)
    auth_token = models.CharField(max_length=40, blank=True, null=True)
    token_expires = models.DateTimeField(blank=True, null=True)
    
    # Campos necessários para o admin
    is_admin = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)  # Agora como campo direto, não como property
    is_superuser = models.BooleanField(default=False)
    
    objects = UserManager()
    
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email', 'name']
    
    def __str__(self):
        return self.name
    
    # Métodos necessários para o admin
    def has_perm(self, perm, obj=None):
        return self.is_admin
    
    def has_module_perms(self, app_label):
        return self.is_admin

class Category(models.Model):
    name = models.CharField(max_length=100)
    
    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=100)
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    barcode = models.CharField(max_length=100, unique=True, blank=True, null=True)
    
    def __str__(self):
        return self.name

class Batch(models.Model):
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.IntegerField()
    inclusion_date = models.DateField(auto_now_add=True)
    expiration_date = models.DateField(blank=True, null=True)
    
    def __str__(self):
        return f"Batch {self.id} - {self.product.name}"

class Inventory(models.Model):
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    batch = models.ForeignKey(Batch, on_delete=models.PROTECT)
    quantity = models.IntegerField()
    
    class Meta:
        unique_together = ('product', 'batch')
    
    def __str__(self):
        return f"{self.quantity} x {self.product} (Batch {self.batch.id})"

class PaymentMethod(models.Model):
    name = models.CharField(max_length=100)
    
    def __str__(self):
        return self.name

class Sale(models.Model):
    sale_datetime = models.DateTimeField(auto_now_add=True)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    addition = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.PROTECT)
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    
    def __str__(self):
        return f"Sale #{self.id} - {self.total_amount}"

class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    units = models.IntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return f"{self.units}x {self.product.name} - {self.total_price}"