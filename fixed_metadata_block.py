            # Update the metadata to indicate sample data
            self.processed_data['metadata'] = {
                'collection_time': datetime.now().isoformat(),
                'data_source': 'sample_generation',
                'total_products': len(self.processed_data['products']),
                'total_brands': len(self.processed_data['brands']),
                'note': 'This data was generated as sample data because website scraping failed. It can be used for testing and demonstration purposes.'
            }
