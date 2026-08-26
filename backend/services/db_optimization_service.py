# 🗃️ Agent World - Database Optimization Service
# Version: 0.4.2 (Épic 8 - Performance)
# Description: Service d'optimisation de la base de données

"""
Database Optimization Service for Agent World.

Ce module fournit des utilitaires pour :
- Analyser les requêtes lentes
- Ajouter des index recommandés
- Optimiser les requêtes SQLAlchemy
- Générer des rapports d'optimisation
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import func, text
from sqlalchemy.orm import Query

from ..models.base import db

logger = logging.getLogger(__name__)


class DBOptimizationService:
    """Service d'optimisation de la base de données."""

    # Index recommandés pour chaque table
    RECOMMENDED_INDEXES = {
        "agents": [
            {
                "columns": ["name"],
                "unique": True,
                "reason": "Recherche fréquente par nom",
            },
            {
                "columns": ["is_active"],
                "reason": "Filtre fréquent sur les agents actifs",
            },
            {
                "columns": ["created_at"],
                "reason": "Tri et pagination par date de création",
            },
            {"columns": ["created_by"], "reason": "Filtre par utilisateur créateur"},
            {"columns": ["project_id"], "reason": "Filtre par projet"},
            {"columns": ["model"], "reason": "Filtre par modèle IA"},
            {
                "columns": ["is_active", "created_at"],
                "reason": "Recherche combinée active + date",
            },
        ],
        "executions": [
            {"columns": ["agent_id"], "reason": "Filtre fréquent par agent"},
            {"columns": ["status"], "reason": "Filtre par statut d'exécution"},
            {"columns": ["created_at"], "reason": "Tri et pagination par date"},
            {"columns": ["executed_by"], "reason": "Filtre par utilisateur exécutant"},
            {"columns": ["workflow_id"], "reason": "Filtre par workflow"},
            {"columns": ["model_used"], "reason": "Filtre par modèle utilisé"},
            {
                "columns": ["agent_id", "created_at"],
                "reason": "Recherche combinée agent + date",
            },
            {
                "columns": ["status", "created_at"],
                "reason": "Recherche combinée statut + date",
            },
            {"columns": ["started_at"], "reason": "Tri par date de démarrage"},
            {"columns": ["completed_at"], "reason": "Tri par date de complétion"},
        ],
        "projects": [
            {
                "columns": ["name"],
                "unique": True,
                "reason": "Recherche par nom de projet",
            },
            {"columns": ["created_by"], "reason": "Filtre par créateur"},
            {"columns": ["created_at"], "reason": "Tri par date de création"},
        ],
        "users": [
            {
                "columns": ["email"],
                "unique": True,
                "reason": "Authentification par email",
            },
            {
                "columns": ["username"],
                "unique": True,
                "reason": "Authentification par username",
            },
            {"columns": ["created_at"], "reason": "Tri par date de création"},
        ],
        "workflows": [
            {"columns": ["name"], "reason": "Recherche par nom de workflow"},
            {"columns": ["agent_id"], "reason": "Filtre par agent associé"},
            {"columns": ["created_at"], "reason": "Tri par date de création"},
            {"columns": ["is_active"], "reason": "Filtre sur les workflows actifs"},
        ],
        "generated_files": [
            {"columns": ["agent_id"], "reason": "Filtre par agent générateur"},
            {"columns": ["execution_id"], "reason": "Filtre par exécution"},
            {"columns": ["created_at"], "reason": "Tri par date de création"},
            {"columns": ["file_format"], "reason": "Filtre par format de fichier"},
            {
                "columns": ["is_temporary"],
                "reason": "Filtre sur les fichiers temporaires",
            },
        ],
        "agent_history": [
            {"columns": ["agent_id"], "reason": "Filtre par agent"},
            {"columns": ["action_type"], "reason": "Filtre par type d'action"},
            {"columns": ["created_at"], "reason": "Tri par date"},
            {"columns": ["author_id"], "reason": "Filtre par auteur"},
        ],
        "templates": [
            {
                "columns": ["name"],
                "unique": True,
                "reason": "Recherche par nom de template",
            },
            {"columns": ["category"], "reason": "Filtre par catégorie"},
            {"columns": ["created_by"], "reason": "Filtre par créateur"},
            {"columns": ["created_at"], "reason": "Tri par date de création"},
            {"columns": ["is_public"], "reason": "Filtre sur les templates publics"},
        ],
    }

    ALLOWED_TABLES = set(RECOMMENDED_INDEXES.keys())

    def __init__(self):
        """Initialise le service d'optimisation de la base de données."""
        self._engine = db.get_engine()

    def get_existing_indexes(self, table_name: str) -> List[Dict[str, Any]]:
        """
        Récupère les index existants pour une table.

        Args:
            table_name: Nom de la table

        Returns:
            Liste des index existants
        """
        try:
            with self._engine.connect() as conn:
                # PostgreSQL
                if self._engine.dialect.name == "postgresql":
                    result = conn.execute(
                        text(
                            """
                        SELECT
                            i.relname as index_name,
                            a.attname as column_name,
                            am.amname as index_type,
                            idx.indisunique as is_unique,
                            idx.indisprimary as is_primary
                        FROM pg_index idx
                        JOIN pg_class i ON i.oid = idx.indexrelid
                        JOIN pg_class t ON t.oid = idx.indrelid
                        JOIN pg_attribute a ON a.attrelid = t.oid AND a.attnum = ANY(idx.indkey)
                        JOIN pg_am am ON i.relam = am.oid
                        WHERE t.relname = :table_name
                        AND idx.indisprimary = false
                        ORDER BY i.relname, a.attnum
                        """
                        )
                        .execution_options(autocommit=False)
                        .bindparams(table_name=table_name)
                    )
                    indexes = []
                    current_index = None
                    for row in result:
                        if (
                            current_index is None
                            or current_index["index_name"] != row.index_name
                        ):
                            current_index = {
                                "name": row.index_name,
                                "columns": [],
                                "type": row.index_type,
                                "unique": row.is_unique,
                                "primary": row.is_primary,
                            }
                            indexes.append(current_index)
                        current_index["columns"].append(row.column_name)
                    return indexes

                # SQLite
                elif self._engine.dialect.name == "sqlite":
                    result = conn.execute(
                        text(
                            "SELECT name, sql FROM sqlite_master WHERE type='index' AND tbl_name=:table_name"
                        ).bindparams(table_name=table_name)
                    )
                    return [
                        {
                            "name": row.name,
                            "sql": row.sql,
                        }
                        for row in result
                    ]

                else:
                    logger.warning(
                        f"⚠️ Unsupported database dialect: {self._engine.dialect.name}"
                    )
                    return []

        except Exception as e:
            logger.error(f"❌ Error getting indexes for table {table_name}: {e}")
            return []

    def get_missing_indexes(
        self, table_name: Optional[str] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Identifie les index manquants pour les tables.

        Args:
            table_name: Nom d'une table spécifique (None = toutes les tables)

        Returns:
            Dictionnaire avec les tables et leurs index manquants
        """
        if table_name is not None:
            self._validate_table_name(table_name)
        tables_to_check = (
            [table_name] if table_name else self.RECOMMENDED_INDEXES.keys()
        )
        missing_indexes = {}

        for table in tables_to_check:
            if table not in self.RECOMMENDED_INDEXES:
                continue

            existing_indexes = self.get_existing_indexes(table)
            existing_columns = set()
            for idx in existing_indexes:
                if "columns" in idx:
                    existing_columns.update(idx["columns"])

            table_missing = []
            for recommended in self.RECOMMENDED_INDEXES[table]:
                columns_set = set(recommended["columns"])
                if not columns_set.issubset(existing_columns):
                    table_missing.append(recommended)

            if table_missing:
                missing_indexes[table] = table_missing

        return missing_indexes

    def _validate_table_name(self, table_name: str) -> None:
        """Validate that table_name is in the allowed whitelist."""
        if table_name not in self.ALLOWED_TABLES:
            raise ValueError(f"Table name '{table_name}' is not allowed")

    def generate_create_index_sql(
        self,
        table_name: str,
        columns: List[str],
        unique: bool = False,
        index_name: Optional[str] = None,
    ) -> str:
        """
        Génère la requête SQL pour créer un index.

        Args:
            table_name: Nom de la table
            columns: Liste des colonnes pour l'index
            unique: Si l'index doit être unique
            index_name: Nom personnalisé pour l'index

        Returns:
            Requête SQL pour créer l'index
        """
        if index_name is None:
            columns_str = "_".join(columns)
            index_name = f"idx_{table_name}_{columns_str}"
            if unique:
                index_name = f"unq_{table_name}_{columns_str}"

        columns_str = ", ".join(columns)
        unique_str = "UNIQUE" if unique else ""

        if self._engine.dialect.name == "postgresql":
            return f"CREATE {unique_str} INDEX {index_name} ON {table_name} ({columns_str})"
        elif self._engine.dialect.name == "sqlite":
            return f"CREATE {unique_str} INDEX IF NOT EXISTS {index_name} ON {table_name} ({columns_str})"
        else:
            return f"CREATE {unique_str} INDEX {index_name} ON {table_name} ({columns_str})"

    def create_missing_indexes(
        self, table_name: Optional[str] = None
    ) -> Dict[str, List[str]]:
        """
        Crée les index manquants pour les tables.

        Args:
            table_name: Nom d'une table spécifique (None = toutes les tables)

        Returns:
            Dictionnaire avec les tables et les index créés
        """
        missing_indexes = self.get_missing_indexes(table_name)
        created_indexes = {}

        for table, indexes in missing_indexes.items():
            created = []
            for idx_config in indexes:
                try:
                    sql = self.generate_create_index_sql(
                        table_name=table,
                        columns=idx_config["columns"],
                        unique=idx_config.get("unique", False),
                    )
                    with self._engine.connect() as conn:
                        conn.execute(text(sql))
                        conn.commit()
                    created.append(sql)
                    logger.info(f"✅ Created index: {sql}")
                except Exception as e:
                    logger.error(
                        f"❌ Failed to create index on {table}({idx_config['columns']}): {e}"
                    )

            if created:
                created_indexes[table] = created

        return created_indexes

    def analyze_slow_queries(self, min_duration_ms: int = 100) -> List[Dict[str, Any]]:
        """
        Analyse les requêtes lentes dans la base de données.

        Args:
            min_duration_ms: Durée minimale pour considérer une requête comme lente

        Returns:
            Liste des requêtes lentes avec des recommandations
        """
        # Pour PostgreSQL, on peut utiliser pg_stat_statements
        if self._engine.dialect.name == "postgresql":
            try:
                with self._engine.connect() as conn:
                    # Activer pg_stat_statements si nécessaire
                    conn.execute(
                        text("CREATE EXTENSION IF NOT EXISTS pg_stat_statements")
                    )
                    conn.commit()

                    result = conn.execute(
                        text(
                            """
                        SELECT
                            query,
                            calls,
                            total_exec_time,
                            mean_exec_time,
                            rows,
                            shared_blks_hit,
                            shared_blks_read
                        FROM pg_stat_statements
                        WHERE mean_exec_time > :min_duration
                        ORDER BY mean_exec_time DESC
                        LIMIT 20
                        """
                        ).bindparams(min_duration=min_duration_ms)
                    )

                    slow_queries = []
                    for row in result:
                        slow_queries.append(
                            {
                                "query": row.query,
                                "calls": row.calls,
                                "total_time_ms": row.total_exec_time,
                                "mean_time_ms": row.mean_exec_time,
                                "rows": row.rows,
                                "blocks_hit": row.shared_blks_hit,
                                "blocks_read": row.shared_blks_read,
                                "recommendations": self._generate_query_recommendations(
                                    row.query
                                ),
                            }
                        )

                    return slow_queries

            except Exception as e:
                logger.error(f"❌ Error analyzing slow queries: {e}")
                return []

        else:
            logger.warning(
                "⚠️ Slow query analysis not supported for this database dialect"
            )
            return []

    def _generate_query_recommendations(self, query: str) -> List[str]:
        """
        Génère des recommandations pour optimiser une requête.

        Args:
            query: Requête SQL à analyser

        Returns:
            Liste de recommandations
        """
        recommendations = []
        query_lower = query.lower()

        # Vérifier les patterns courants
        if "where" in query_lower and "order by" in query_lower:
            if "index" not in query_lower:
                recommendations.append(
                    "Add an index on the columns used in WHERE and ORDER BY clauses"
                )

        if "join" in query_lower:
            recommendations.append("Ensure join columns are indexed")

        if "like" in query_lower:
            recommendations.append(
                "Consider using a full-text search index for LIKE patterns"
            )

        if "select *" in query_lower:
            recommendations.append("Avoid SELECT * - specify only needed columns")

        if "offset" in query_lower and "limit" in query_lower:
            recommendations.append(
                "For large offsets, consider using keyset pagination instead"
            )

        if "count(*)" in query_lower:
            recommendations.append(
                "For large tables, consider storing counts in a separate table"
            )

        return recommendations

    def optimize_query(self, query: Query) -> Query:
        """
        Optimise une requête SQLAlchemy.

        Args:
            query: Requête SQLAlchemy à optimiser

        Returns:
            Requête optimisée
        """
        # Ajouter des options d'optimisation standard
        return query

    def get_table_statistics(self, table_name: str) -> Dict[str, Any]:
        """
        Récupère les statistiques pour une table.

        Args:
            table_name: Nom de la table

        Returns:
            Dictionnaire avec les statistiques
        """
        self._validate_table_name(table_name)
        try:
            if self._engine.dialect.name == "postgresql":
                with self._engine.connect() as conn:
                    # Taille de la table
                    size_result = conn.execute(
                        text(
                            """
                        SELECT
                            pg_size_pretty(pg_total_relation_size(:table)) as total_size,
                            pg_size_pretty(pg_table_size(:table)) as table_size,
                            pg_size_pretty(pg_indexes_size(:table)) as indexes_size,
                            pg_total_relation_size(:table) as total_bytes,
                            pg_table_size(:table) as table_bytes,
                            pg_indexes_size(:table) as indexes_bytes
                        FROM pg_stat_user_tables
                        WHERE relname = :table
                        """
                        ).bindparams(table=table_name)
                    ).first()

                    # Nombre de lignes
                    count_result = conn.execute(
                        text("SELECT COUNT(*) as row_count FROM " + table_name)
                    ).first()

                    # Statistiques d'utilisation
                    stats_result = conn.execute(
                        text(
                            """
                        SELECT
                            n_live_tup as live_rows,
                            n_dead_tup as dead_rows,
                            last_vacuum,
                            last_analyze,
                            last_autoanalyze
                        FROM pg_stat_user_tables
                        WHERE relname = :table
                        """
                        ).bindparams(table=table_name)
                    ).first()

                    return {
                        "table": table_name,
                        "size": {
                            "total": size_result.total_size if size_result else "N/A",
                            "table": size_result.table_size if size_result else "N/A",
                            "indexes": (
                                size_result.indexes_size if size_result else "N/A"
                            ),
                            "total_bytes": (
                                size_result.total_bytes if size_result else 0
                            ),
                            "table_bytes": (
                                size_result.table_bytes if size_result else 0
                            ),
                            "indexes_bytes": (
                                size_result.indexes_bytes if size_result else 0
                            ),
                        },
                        "rows": {
                            "total": count_result.row_count if count_result else 0,
                            "live": stats_result.live_rows if stats_result else 0,
                            "dead": stats_result.dead_rows if stats_result else 0,
                        },
                        "maintenance": {
                            "last_vacuum": (
                                stats_result.last_vacuum if stats_result else None
                            ),
                            "last_analyze": (
                                stats_result.last_analyze if stats_result else None
                            ),
                            "last_autoanalyze": (
                                stats_result.last_autoanalyze if stats_result else None
                            ),
                        },
                    }

            elif self._engine.dialect.name == "sqlite":
                with self._engine.connect() as conn:
                    count_result = conn.execute(
                        text("SELECT COUNT(*) as row_count FROM " + table_name)
                    ).first()

                    return {
                        "table": table_name,
                        "rows": {
                            "total": count_result.row_count if count_result else 0,
                        },
                    }

            else:
                logger.warning(
                    f"⚠️ Table statistics not fully supported for {self._engine.dialect.name}"
                )
                return {"table": table_name}

        except Exception as e:
            logger.error(f"❌ Error getting statistics for table {table_name}: {e}")
            return {"table": table_name, "error": str(e)}

    def generate_optimization_report(self) -> Dict[str, Any]:
        """
        Génère un rapport complet d'optimisation de la base de données.

        Returns:
            Dictionnaire avec le rapport d'optimisation
        """
        report = {
            "generated_at": datetime.utcnow().isoformat(),
            "database_type": self._engine.dialect.name,
            "tables": {},
            "slow_queries": [],
            "recommendations": [],
        }

        # Analyser chaque table
        for table_name in self.RECOMMENDED_INDEXES.keys():
            try:
                table_stats = self.get_table_statistics(table_name)
                missing_indexes = self.get_missing_indexes(table_name)

                report["tables"][table_name] = {
                    "statistics": table_stats,
                    "missing_indexes": missing_indexes.get(table_name, []),
                }

                # Ajouter des recommandations pour les tables sans index
                if missing_indexes.get(table_name):
                    report["recommendations"].append(
                        f"Create missing indexes on table '{table_name}': "
                        f"{len(missing_indexes[table_name])} indexes needed"
                    )

            except Exception as e:
                logger.error(f"❌ Error analyzing table {table_name}: {e}")
                report["tables"][table_name] = {"error": str(e)}

        # Analyser les requêtes lentes
        slow_queries = self.analyze_slow_queries()
        report["slow_queries"] = slow_queries

        if slow_queries:
            report["recommendations"].append(
                f"Optimize {len(slow_queries)} slow queries identified"
            )

        # Ajouter des recommandations générales
        report["recommendations"].extend(
            [
                "Add indexes on frequently filtered and sorted columns",
                "Consider using connection pooling for better performance",
                "Regularly run VACUUM and ANALYZE on PostgreSQL tables",
                "Monitor query performance with pg_stat_statements (PostgreSQL)",
            ]
        )

        return report

    def create_optimization_migration(
        self, output_file: str = "migrations/optimize_db.py"
    ) -> bool:
        """
        Crée un fichier de migration pour optimiser la base de données.

        Args:
            output_file: Chemin du fichier de migration

        Returns:
            True si le fichier a été créé, False sinon
        """
        try:
            missing_indexes = self.get_missing_indexes()

            if not missing_indexes:
                logger.info("✅ No missing indexes to create")
                return False

            # Générer le contenu du fichier de migration
            migration_content = f'''# Alembic Migration: Optimize Database Indexes
# Generated by DBOptimizationService on {datetime.utcnow().isoformat()}

from alembic import op
import sqlalchemy as sa


def upgrade():
    """Create recommended indexes for performance optimization."""
'''

            for table_name, indexes in missing_indexes.items():
                for idx_config in indexes:
                    columns = idx_config["columns"]
                    unique = idx_config.get("unique", False)
                    index_name = f"idx_{table_name}_{'_'.join(columns)}"
                    index_sql = self.generate_create_index_sql(
                        table_name, columns, unique, index_name=index_name
                    )
                    migration_content += f"""    # {table_name} - {idx_config['reason']}
    op.create_index(
        '{index_sql}'
    )
"""

            migration_content += '''

def downgrade():
    """Remove created indexes."""
'''

            # Ajouter le downgrade (inverse du upgrade)
            for table_name, indexes in missing_indexes.items():
                for idx_config in indexes:
                    columns = idx_config["columns"]
                    index_name = f"idx_{table_name}_{'_'.join(columns)}"
                    migration_content += f"""    op.drop_index({index_name!r}, table_name={table_name!r})
"""

            migration_content += """
"""

            # Écrire le fichier
            import os

            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            with open(output_file, "w") as f:
                f.write(migration_content)

            logger.info(f"✅ Created optimization migration: {output_file}")
            return True

        except Exception as e:
            logger.error(f"❌ Error creating optimization migration: {e}")
            return False

    def run_vacuum_analyze(self, table_name: Optional[str] = None) -> bool:
        """
        Exécute VACUUM ANALYZE sur les tables (PostgreSQL uniquement).

        Args:
            table_name: Nom d'une table spécifique (None = toutes les tables)

        Returns:
            True si succès, False sinon
        """
        if self._engine.dialect.name != "postgresql":
            logger.warning("⚠️ VACUUM ANALYZE is only supported on PostgreSQL")
            return False

        try:
            if table_name:
                self._validate_table_name(table_name)
                with self._engine.connect() as conn:
                    conn.execute(text("VACUUM ANALYZE " + table_name))
                    conn.commit()
                logger.info(f"✅ VACUUM ANALYZE executed on table {table_name}")
            else:
                with self._engine.connect() as conn:
                    conn.execute(text("VACUUM ANALYZE"))
                    conn.commit()
                logger.info("✅ VACUUM ANALYZE executed on all tables")
            return True

        except Exception as e:
            logger.error(f"❌ Error running VACUUM ANALYZE: {e}")
            return False


# Instance globale du service
_db_optimization_service: Optional[DBOptimizationService] = None


def get_db_optimization_service() -> DBOptimizationService:
    """Retourne l'instance globale du service d'optimisation de la base de données."""
    global _db_optimization_service
    if _db_optimization_service is None:
        _db_optimization_service = DBOptimizationService()
    return _db_optimization_service
