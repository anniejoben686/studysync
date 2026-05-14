from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lms_core', '0003_add_gender_phone_to_student_profile'),
    ]

    operations = [
        # Drop the old score and attempted_on columns, add new ones
        migrations.RemoveField(
            model_name='quizattempt',
            name='score',
        ),
        migrations.RemoveField(
            model_name='quizattempt',
            name='attempted_on',
        ),
        migrations.AddField(
            model_name='quizattempt',
            name='marks_obtained',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='quizattempt',
            name='total_marks',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='quizattempt',
            name='percentage',
            field=models.FloatField(default=0.0),
        ),
        migrations.AddField(
            model_name='quizattempt',
            name='attempt_number',
            field=models.IntegerField(default=1),
        ),
        migrations.AddField(
            model_name='quizattempt',
            name='is_best',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='quizattempt',
            name='submitted_at',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AlterModelOptions(
            name='quizattempt',
            options={'ordering': ['-submitted_at']},
        ),
    ]
