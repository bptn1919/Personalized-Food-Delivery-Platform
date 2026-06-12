from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("recommendation", "0002_alter_userfoodpreferencefeature_diet_level_and_more"),
    ]

    operations = [
        migrations.RunSQL(
            sql="CREATE EXTENSION IF NOT EXISTS vector;",
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            sql="""
                CREATE TABLE IF NOT EXISTS recommendation_dish_vector_index (
                    dish_uid uuid PRIMARY KEY REFERENCES dish_dish(uid) ON DELETE CASCADE,
                    embedding vector(5) NOT NULL,
                    confidence real NOT NULL DEFAULT 1.0,
                    updated_at timestamptz NOT NULL DEFAULT NOW()
                );
            """,
            reverse_sql="DROP TABLE IF EXISTS recommendation_dish_vector_index;",
        ),
        migrations.RunSQL(
            sql="""
                CREATE TABLE IF NOT EXISTS recommendation_user_vector_index (
                    user_id bigint PRIMARY KEY REFERENCES users_customuser(id) ON DELETE CASCADE,
                    embedding vector(5) NOT NULL,
                    confidence real NOT NULL DEFAULT 0.0,
                    updated_at timestamptz NOT NULL DEFAULT NOW()
                );
            """,
            reverse_sql="DROP TABLE IF EXISTS recommendation_user_vector_index;",
        ),
        migrations.RunSQL(
            sql="""
                CREATE INDEX IF NOT EXISTS rec_dish_vec_ivfflat_cos_idx
                ON recommendation_dish_vector_index
                USING ivfflat (embedding vector_cosine_ops)
                WITH (lists = 100);
            """,
            reverse_sql="DROP INDEX IF EXISTS rec_dish_vec_ivfflat_cos_idx;",
        ),
        migrations.RunSQL(
            sql="""
                DO $$
                BEGIN
                    BEGIN
                        CREATE INDEX IF NOT EXISTS rec_dish_vec_hnsw_cos_idx
                        ON recommendation_dish_vector_index
                        USING hnsw (embedding vector_cosine_ops);
                    EXCEPTION
                        WHEN OTHERS THEN
                            NULL;
                    END;
                END
                $$;
            """,
            reverse_sql="DROP INDEX IF EXISTS rec_dish_vec_hnsw_cos_idx;",
        ),
    ]
