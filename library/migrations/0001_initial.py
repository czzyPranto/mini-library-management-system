# Initial migration for the four custom library models.
from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import library.validators


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Author',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=120, unique=True)),
                ('email', models.EmailField(blank=True, max_length=254)),
                ('bio', models.TextField(blank=True)),
            ],
            options={'ordering': ['name']},
        ),
        migrations.CreateModel(
            name='MemberProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('membership_id', models.CharField(max_length=8, unique=True, validators=[library.validators.validate_membership_id])),
                ('phone', models.CharField(blank=True, max_length=20)),
                ('joined_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='member_profile', to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['membership_id'], 'verbose_name': 'Member profile'},
        ),
        migrations.CreateModel(
            name='Book',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('isbn', models.CharField(max_length=13, unique=True, validators=[library.validators.validate_isbn13])),
                ('genre', models.CharField(choices=[('programming', 'Programming'), ('fiction', 'Fiction'), ('science', 'Science'), ('other', 'Other')], default='other', max_length=20)),
                ('total_copies', models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])),
                ('published_year', models.PositiveIntegerField(blank=True, null=True)),
                ('authors', models.ManyToManyField(related_name='books', to='library.author')),
            ],
            options={'ordering': ['title']},
        ),
        migrations.CreateModel(
            name='BorrowRecord',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('borrow_date', models.DateField(default=django.utils.timezone.localdate)),
                ('due_date', models.DateField()),
                ('returned_at', models.DateField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('book', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='loans', to='library.book')),
                ('member', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='loans', to='library.memberprofile')),
            ],
            options={'ordering': ['-borrow_date', '-id']},
        ),
    ]
