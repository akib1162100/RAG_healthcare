"""
ETL Pipeline Orchestrator for Medical Data
Coordinates extraction, transformation, embedding, and loading
"""
import os
import asyncio
import argparse
from datetime import datetime, timedelta
from typing import Optional
import logging

from sqlalchemy.ext.asyncio import create_async_engine
from app.core.config import settings
from .data_extractor import OdooDataExtractor
from .data_transformer import MedicalDataTransformer
from .embedding_generator import MedicalEmbeddingGenerator
from .vector_loader import VectorLoader

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ETLPipeline:
    """Main ETL pipeline orchestrator"""
    
    def __init__(self):
        # Initialize components
        self.engine = create_async_engine(settings.DATABASE_URL, echo=False)
        
        self.extractor = OdooDataExtractor(None, self.engine)
        self.transformer = MedicalDataTransformer(
            chunk_size=int(os.getenv('ETL_CHUNK_SIZE', '800')),
            chunk_overlap=int(os.getenv('ETL_CHUNK_OVERLAP', '150'))
        )
        self.embedding_generator = MedicalEmbeddingGenerator()
        self.loader = VectorLoader(self.engine)
    
    async def run_appointment_indexing(
        self,
        limit: Optional[int] = None,
        incremental: bool = False
    ) -> dict:
        """Index appointment data"""
        logger.info("Starting appointment indexing...")
        
        # Get last indexed date for incremental updates
        since_date = None
        if incremental:
            since_date = await self.extractor.get_last_indexed_date('wk.appointment')
            if since_date:
                logger.info(f"Incremental update since: {since_date}")
        
        # Extract appointments
        appointments = await self.extractor.extract_appointments(
            limit=limit,
            since_date=since_date,
            incremental=incremental
        )
        
        if not appointments:
            logger.info("No appointments to index")
            return {'records_indexed': 0, 'chunks_created': 0, 'data': []}
        
        # Transform
        record_data = []
        for appointment in appointments:
            text, metadata = self.transformer.flatten_appointment(appointment)
            record_data.append((appointment['id'], text, metadata))
            
        # Generate embeddings in batches
        texts = [data[1] for data in record_data]
        embeddings = self.embedding_generator.generate_embeddings(
            texts,
            batch_size=int(os.getenv('ETL_BATCH_SIZE', '32'))
        )
        
        # Prepare for loading
        vectors_to_load = []
        for (res_id, text, metadata), embedding in zip(record_data, embeddings):
            vectors_to_load.append((
                'wk.appointment',
                res_id,
                0,
                text,
                metadata,
                embedding
            ))
        
        # Load vectors in batches
        batch_size = 100
        chunks_created = 0
        for i in range(0, len(vectors_to_load), batch_size):
            batch = vectors_to_load[i:i+batch_size]
            chunks_created += await self.loader.load_vectors(batch)
        
        # Update ETL metadata
        if appointments:
            # Parse write_date strings if they aren't already datetime objects
            processed_dates = []
            for a in appointments:
                wd = a.get('write_date')
                if isinstance(wd, str):
                    try:
                        processed_dates.append(datetime.fromisoformat(wd.replace('Z', '+00:00')))
                    except ValueError:
                        processed_dates.append(datetime.now())
                elif isinstance(wd, datetime):
                    processed_dates.append(wd)
                else:
                    processed_dates.append(datetime.now())
            
            last_write_date = max(processed_dates) if processed_dates else datetime.now()
            
            await self.extractor.update_etl_metadata(
                'wk.appointment',
                last_write_date,
                len(appointments),
                chunks_created
            )
            
            # Mark synced in Odoo
            record_ids = [a['id'] for a in appointments]
            await self.extractor.mark_records_as_synced('wk.appointment', record_ids)
        
        logger.info(f"Indexed {len(appointments)} appointments, created {chunks_created} chunks")
        return {
            'records_indexed': len(appointments), 
            'chunks_created': chunks_created,
            'data': appointments
        }

    async def run_patient_indexing(
        self,
        limit: Optional[int] = None,
        incremental: bool = False
    ) -> dict:
        """Index patient data"""
        logger.info("Starting patient indexing...")
        
        patients = await self.extractor.extract_patients(
            limit=limit,
            incremental=incremental
        )
        
        if not patients:
            logger.info("No patients to index")
            return {'records_indexed': 0, 'chunks_created': 0, 'data': []}
            
        # Transform
        record_data = []
        for patient in patients:
            text, metadata = self.transformer.flatten_patient(patient)
            record_data.append((patient['id'], text, metadata))
            
        # Generate embeddings in batches
        texts = [data[1] for data in record_data]
        embeddings = self.embedding_generator.generate_embeddings(
            texts,
            batch_size=int(os.getenv('ETL_BATCH_SIZE', '32'))
        )
        
        # Prepare for loading
        vectors_to_load = []
        for (res_id, text, metadata), embedding in zip(record_data, embeddings):
            vectors_to_load.append((
                'res.partner',
                res_id,
                0,
                text,
                metadata,
                embedding
            ))
            
        # Load vectors in batches
        batch_size = 100
        chunks_created = 0
        for i in range(0, len(vectors_to_load), batch_size):
            batch = vectors_to_load[i:i+batch_size]
            chunks_created += await self.loader.load_vectors(batch)
        
        if patients:
            # Parse write_date strings
            processed_dates = []
            for p in patients:
                wd = p.get('write_date')
                if isinstance(wd, str):
                    try:
                        processed_dates.append(datetime.fromisoformat(wd.replace('Z', '+00:00')))
                    except ValueError:
                        processed_dates.append(datetime.now())
                elif isinstance(wd, datetime):
                    processed_dates.append(wd)
                else:
                    processed_dates.append(datetime.now())
            
            last_write_date = max(processed_dates) if processed_dates else datetime.now()
            
            await self.extractor.update_etl_metadata(
                'res.partner',
                last_write_date,
                len(patients),
                chunks_created
            )
            
            record_ids = [p['id'] for p in patients]
            await self.extractor.mark_records_as_synced('res.partner', record_ids)
            
        logger.info(f"Indexed {len(patients)} patients")
        return {
            'records_indexed': len(patients),
            'chunks_created': chunks_created,
            'data': patients
        }

    async def run_disease_indexing(
        self,
        limit: Optional[int] = None
    ) -> dict:
        """Index disease data"""
        logger.info("Starting disease indexing...")
        
        # Diseases are usually full sync
        diseases = await self.extractor.extract_diseases(limit=limit)
        
        if not diseases:
            logger.info("No diseases to index")
            return {'records_indexed': 0, 'chunks_created': 0, 'data': []}
            
        # Transform
        record_data = []
        for disease in diseases:
            text, metadata = self.transformer.flatten_disease(disease)
            record_data.append((disease['id'], text, metadata))
            
        # Generate embeddings in batches
        # For very large datasets like diseases, we do this in bigger batches
        logger.info(f"Generating embeddings for {len(diseases)} diseases...")
        texts = [data[1] for data in record_data]
        embeddings = self.embedding_generator.generate_embeddings(
            texts,
            batch_size=128 # Higher batch size for simpler texts
        )
        
        # Prepare for loading
        vectors_to_load = []
        for (res_id, text, metadata), embedding in zip(record_data, embeddings):
            vectors_to_load.append((
                'medical.disease',
                res_id,
                0,
                text,
                metadata,
                embedding
            ))
            
        # Load vectors in batches
        batch_size = 500
        chunks_created = 0
        for i in range(0, len(vectors_to_load), batch_size):
            batch = vectors_to_load[i:i+batch_size]
            chunks_created += await self.loader.load_vectors(batch)
            if (i // batch_size) % 10 == 0:
                logger.info(f"Loaded {i + len(batch)}/{len(vectors_to_load)} diseases...")
        
        logger.info(f"Indexed {len(diseases)} diseases")
        return {
            'records_indexed': len(diseases),
            'chunks_created': chunks_created,
            'data': diseases
        }
    
    async def run_prescription_indexing(
        self,
        limit: Optional[int] = None,
        incremental: bool = False
    ) -> dict:
        """Index prescription data"""
        logger.info("Starting prescription indexing...")
        
        # Get last indexed date for incremental updates
        since_date = None
        if incremental:
            since_date = await self.extractor.get_last_indexed_date('prescription.order.knk')
            if since_date:
                logger.info(f"Incremental update since: {since_date}")
        
        # Extract prescriptions
        prescriptions = await self.extractor.extract_prescriptions(
            limit=limit,
            since_date=since_date,
            incremental=incremental
        )
        
        if not prescriptions:
            logger.info("No prescriptions to index")
            return {'records_indexed': 0, 'chunks_created': 0, 'data': []}
        
        # Transform and embed
        vectors_to_load = []
        total_chunks = 0
        
        for prescription in prescriptions:
            # Transform (may return multiple chunks)
            chunks_with_metadata = self.transformer.flatten_prescription(prescription)
            
            # Generate embeddings for all chunks
            texts = [chunk for chunk, _ in chunks_with_metadata]
            embeddings = self.embedding_generator.generate_embeddings(
                texts,
                batch_size=int(os.getenv('ETL_BATCH_SIZE', '32'))
            )
            
            # Prepare for loading
            for (text, metadata), embedding in zip(chunks_with_metadata, embeddings):
                vectors_to_load.append((
                    'prescription.order.knk',
                    prescription['id'],
                    metadata['chunk_index'],
                    text,
                    metadata,
                    embedding
                ))
                total_chunks += 1
        
        # Load vectors in batches
        batch_size = 100
        chunks_loaded = 0
        for i in range(0, len(vectors_to_load), batch_size):
            batch = vectors_to_load[i:i+batch_size]
            chunks_loaded += await self.loader.load_vectors(batch)
        
        # Update ETL metadata
        if prescriptions:
            # Parse write_date strings
            processed_dates = []
            for p in prescriptions:
                wd = p.get('write_date')
                if isinstance(wd, str):
                    try:
                        processed_dates.append(datetime.fromisoformat(wd.replace('Z', '+00:00')))
                    except ValueError:
                        processed_dates.append(datetime.now())
                elif isinstance(wd, datetime):
                    processed_dates.append(wd)
                else:
                    processed_dates.append(datetime.now())
            
            last_write_date = max(processed_dates) if processed_dates else datetime.now()

            await self.extractor.update_etl_metadata(
                'prescription.order.knk',
                last_write_date,
                len(prescriptions),
                chunks_loaded
            )
            
            # Mark synced in Odoo
            record_ids = [p['id'] for p in prescriptions]
            await self.extractor.mark_records_as_synced('prescription.order.knk', record_ids)
        
        logger.info(f"Indexed {len(prescriptions)} prescriptions, created {chunks_loaded} chunks")
        return {
            'records_indexed': len(prescriptions), 
            'chunks_created': chunks_loaded,
            'data': prescriptions
        }
    
    async def run_full_indexing(
        self,
        models: list = None,
        limit: Optional[int] = None,
        incremental: bool = False
    ) -> dict:
        """Run indexing for multiple models"""
        if models is None:
            models = ['wk.appointment', 'prescription.order.knk']
        
        results = {}
        
        for model in models:
            if model == 'wk.appointment':
                results[model] = await self.run_appointment_indexing(limit, incremental)
            elif model == 'prescription.order.knk':
                results[model] = await self.run_prescription_indexing(limit, incremental)
            elif model == 'res.partner':
                results[model] = await self.run_patient_indexing(limit, incremental)
            elif model == 'medical.disease':
                results[model] = await self.run_disease_indexing(limit)
            else:
                logger.warning(f"Unknown model: {model}")
        
        return results
    
    async def get_index_status(self) -> dict:
        """Get current indexing status"""
        stats = await self.loader.get_index_stats()
        
        # Get ETL metadata
        query = "SELECT * FROM etl_metadata"
        async with self.engine.connect() as conn:
            from sqlalchemy import text
            result = await conn.execute(text(query))
            rows = result.fetchall()
            
            etl_metadata = {}
            for row in rows:
                etl_metadata[row.odoo_model] = {
                    'last_indexed_at': row.last_indexed_at.isoformat() if row.last_indexed_at else None,
                    'last_write_date': row.last_write_date.isoformat() if row.last_write_date else None,
                    'total_records': row.total_records,
                    'total_chunks': row.total_chunks
                }
        
        return {
            'index_stats': stats,
            'etl_metadata': etl_metadata
        }
    
    async def close(self):
        """Close database connections"""
        await self.engine.dispose()


async def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(description='ETL Pipeline for Medical Data')
    parser.add_argument('--model', type=str, choices=['wk.appointment', 'prescription.order.knk', 'all'],
                        default='all', help='Model to index')
    parser.add_argument('--limit', type=int, help='Limit number of records')
    parser.add_argument('--incremental', action='store_true', default=True,
                        help='Incremental update (only new/modified records)')
    parser.add_argument('--full-reindex', action='store_true',
                        help='Full reindex (ignore last indexed date)')
    parser.add_argument('--status', action='store_true',
                        help='Show indexing status')
    
    args = parser.parse_args()
    
    pipeline = ETLPipeline()
    
    try:
        if args.status:
            status = await pipeline.get_index_status()
            print("\n=== Indexing Status ===")
            print(f"\nIndex Stats: {status['index_stats']}")
            print(f"\nETL Metadata: {status['etl_metadata']}")
        else:
            incremental = not args.full_reindex
            
            if args.model == 'all':
                results = await pipeline.run_full_indexing(
                    limit=args.limit,
                    incremental=incremental
                )
            else:
                results = await pipeline.run_full_indexing(
                    models=[args.model],
                    limit=args.limit,
                    incremental=incremental
                )
            
            print("\n=== Indexing Results ===")
            for model, result in results.items():
                print(f"\n{model}:")
                print(f"  Records indexed: {result['records_indexed']}")
                print(f"  Chunks created: {result['chunks_created']}")
    
    finally:
        await pipeline.close()


if __name__ == '__main__':
    asyncio.run(main())
