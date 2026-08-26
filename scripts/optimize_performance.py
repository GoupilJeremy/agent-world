#!/usr/bin/env python3
# 🚀 Agent World - Performance Optimization Script
# Version: 0.4.2 (Épic 8)
# Description: Script pour optimiser les performances de l'application

"""
Performance Optimization Script for Agent World.

Ce script permet de :
1. Créer les index manquants dans la base de données
2. Exécuter VACUUM ANALYZE sur les tables
3. Tester la connexion Redis
4. Générer un rapport d'optimisation complet
5. Configurer automatiquement les optimisations
"""

import argparse
import json
import logging
import sys
from datetime import datetime

# Ajouter le chemin du backend au path
sys.path.insert(0, '/c/dev/agent-world/agent-world')

from backend.app import create_app
from backend.services.db_optimization_service import get_db_optimization_service
from backend.services.cache_service import get_cache_service
from backend.services.agent_cache_service import get_agent_cache_service

# Configurer le logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_redis_connection():
    """Test la connexion Redis."""
    logger.info("🔍 Testing Redis connection...")
    cache_service = get_cache_service()
    
    if cache_service.is_available():
        logger.info("✅ Redis connection successful")
        try:
            client = cache_service.client
            info = client.info()
            logger.info(f"   Redis version: {info.get('redis_version', 'N/A')}")
            logger.info(f"   Uptime: {info.get('uptime_in_seconds', 0)} seconds")
            logger.info(f"   Memory used: {info.get('used_memory_human', 'N/A')}")
            return True
        except Exception as e:
            logger.error(f"❌ Error getting Redis info: {e}")
            return False
    else:
        logger.warning("⚠️ Redis is not available. Cache will be disabled.")
        return False


def create_missing_indexes(yes: bool = False):
    """Crée les index manquants dans la base de données."""
    logger.info("🔍 Checking for missing database indexes...")
    db_optimization = get_db_optimization_service()
    
    missing_indexes = db_optimization.get_missing_indexes()
    
    if not missing_indexes:
        logger.info("✅ No missing indexes found")
        return True
    
    logger.info(f"📋 Found {len(missing_indexes)} tables with missing indexes:")
    for table, indexes in missing_indexes.items():
        logger.info(f"   Table '{table}': {len(indexes)} missing indexes")
        for idx in indexes:
            logger.info(f"      - {idx['columns']} ({idx['reason']})")
    
    if yes or input("\n❓ Do you want to create these indexes? [y/N]: ").lower() == 'y':
        logger.info("🔨 Creating missing indexes...")
        created = db_optimization.create_missing_indexes()
        
        for table, indexes in created.items():
            logger.info(f"   ✅ Created {len(indexes)} indexes on '{table}'")
            for sql in indexes:
                logger.debug(f"      {sql}")
        
        logger.info("✅ Database indexes created successfully")
        return True
    else:
        logger.info("⏹️ Index creation cancelled")
        return False


def run_vacuum_analyze(yes: bool = False):
    """Exécute VACUUM ANALYZE sur la base de données."""
    logger.info("🔍 Running VACUUM ANALYZE...")
    db_optimization = get_db_optimization_service()
    
    if yes or input("❓ Do you want to run VACUUM ANALYZE on all tables? [y/N]: ").lower() == 'y':
        success = db_optimization.run_vacuum_analyze()
        if success:
            logger.info("✅ VACUUM ANALYZE completed successfully")
            return True
        else:
            logger.warning("⚠️ VACUUM ANALYZE not supported or failed")
            return False
    else:
        logger.info("⏹️ VACUUM ANALYZE cancelled")
        return False


def generate_optimization_report(output_file: str = None):
    """Génère un rapport d'optimisation complet."""
    logger.info("📊 Generating optimization report...")
    db_optimization = get_db_optimization_service()
    
    report = db_optimization.generate_optimization_report()
    
    # Ajouter les stats du cache
    cache_service = get_cache_service()
    report["cache"] = {
        "available": cache_service.is_available(),
        "agent_cache": get_agent_cache_service().get_cache_stats()
    }
    
    # Afficher le rapport
    logger.info("\n" + "=" * 60)
    logger.info("📊 PERFORMANCE OPTIMIZATION REPORT")
    logger.info("=" * 60)
    logger.info(f"Generated: {report['generated_at']}")
    logger.info(f"Database: {report['database_type']}")
    
    logger.info("\n📋 Table Statistics:")
    for table_name, table_data in report['tables'].items():
        if 'error' in table_data:
            logger.warning(f"   {table_name}: Error - {table_data['error']}")
            continue
        
        stats = table_data.get('statistics', {})
        missing = table_data.get('missing_indexes', [])
        
        if 'rows' in stats:
            logger.info(f"   {table_name}:")
            logger.info(f"      Rows: {stats['rows'].get('total', 'N/A')}")
            if 'size' in stats:
                logger.info(f"      Size: {stats['size'].get('total', 'N/A')}")
        
        if missing:
            logger.warning(f"      ⚠️ Missing indexes: {len(missing)}")
    
    logger.info("\n💡 Recommendations:")
    for i, recommendation in enumerate(report['recommendations'], 1):
        logger.info(f"   {i}. {recommendation}")
    
    logger.info("\n" + "=" * 60)
    
    # Sauvegarder dans un fichier si demandé
    if output_file:
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        logger.info(f"✅ Report saved to: {output_file}")
    
    return report


def check_performance_endpoints():
    """Test les endpoints de performance."""
    logger.info("🔍 Testing performance endpoints...")
    
    # Créer une application de test
    app = create_app()
    
    with app.app_context():
        with app.test_client() as client:
            # Tester l'endpoint de cache
            try:
                response = client.get('/api/performance/cache/stats')
                if response.status_code == 200:
                    logger.info("   ✅ /api/performance/cache/stats - OK")
                else:
                    logger.warning(f"   ⚠️ /api/performance/cache/stats - {response.status_code}")
            except Exception as e:
                logger.error(f"   ❌ /api/performance/cache/stats - {e}")
            
            # Tester l'endpoint d'optimisation BDD
            try:
                response = client.get('/api/performance/db/optimize')
                if response.status_code == 200:
                    logger.info("   ✅ /api/performance/db/optimize - OK")
                else:
                    logger.warning(f"   ⚠️ /api/performance/db/optimize - {response.status_code}")
            except Exception as e:
                logger.error(f"   ❌ /api/performance/db/optimize - {e}")


def main():
    """Point d'entrée principal du script."""
    parser = argparse.ArgumentParser(
        description='Agent World - Performance Optimization Script',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python optimize_performance.py --check           Check performance status
  python optimize_performance.py --optimize       Run all optimizations
  python optimize_performance.py --report out.json  Generate optimization report
  python optimize_performance.py --all            Run all operations
        """
    )
    
    parser.add_argument(
        '--check', '-c',
        action='store_true',
        help='Check performance status (Redis, DB indexes)'
    )
    parser.add_argument(
        '--optimize', '-o',
        action='store_true',
        help='Run all optimizations (indexes + vacuum)'
    )
    parser.add_argument(
        '--indexes', '-i',
        action='store_true',
        help='Create missing database indexes'
    )
    parser.add_argument(
        '--vacuum', '-v',
        action='store_true',
        help='Run VACUUM ANALYZE on database'
    )
    parser.add_argument(
        '--report', '-r',
        metavar='FILE',
        help='Generate optimization report and save to file'
    )
    parser.add_argument(
        '--test-endpoints', '-t',
        action='store_true',
        help='Test performance endpoints'
    )
    parser.add_argument(
        '--all', '-a',
        action='store_true',
        help='Run all operations (check + optimize + report)'
    )
    parser.add_argument(
        '--yes', '-y',
        action='store_true',
        help='Answer yes to all prompts'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    logger.info("=" * 60)
    logger.info("🚀 Agent World - Performance Optimization Script")
    logger.info("=" * 60)
    logger.info(f"📅 {datetime.utcnow().isoformat()}")
    logger.info("")
    
    # Créer l'application Flask
    app = create_app()
    
    with app.app_context():
        try:
            # Test Redis
            redis_ok = test_redis_connection()
            logger.info("")
            
            if args.all or args.check or args.optimize or args.indexes:
                # Vérifier les index
                if args.all or args.indexes or (args.optimize and not args.vacuum):
                    create_missing_indexes(args.yes)
                    logger.info("")
                
                if args.all or args.vacuum or (args.optimize and args.vacuum):
                    run_vacuum_analyze(args.yes)
                    logger.info("")
            
            if args.all or args.report:
                generate_optimization_report(args.report)
                logger.info("")
            
            if args.all or args.test_endpoints:
                check_performance_endpoints()
                logger.info("")
            
            if not any([args.check, args.optimize, args.indexes, args.vacuum, args.report, args.test_endpoints, args.all]):
                # Afficher l'aide
                parser.print_help()
                
            logger.info("=" * 60)
            logger.info("✅ Performance optimization completed")
            logger.info("=" * 60)
            
            return 0
            
        except KeyboardInterrupt:
            logger.info("\n⏹️ Operation cancelled by user")
            return 1
        except Exception as e:
            logger.error(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return 1


if __name__ == '__main__':
    sys.exit(main())
