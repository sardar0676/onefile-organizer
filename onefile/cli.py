"""
Command-line interface for onefile.
"""
import argparse
import sys
import json
import logging
import os
from pathlib import Path
from typing import Optional, Dict, Any, List

from .core import FileOrganizer, organize_folder
from .watcher import run_daemon, FileWatcher

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('onefile.log')
    ]
)
logger = logging.getLogger(__name__)

class OneFileCLI:
    """Command-line interface for onefile."""
    
    def __init__(self):
        """Initialize the CLI parser."""
        self.parser = self._create_parser()
    
    def _create_parser(self) -> argparse.ArgumentParser:
        """Create and configure the argument parser."""
        parser = argparse.ArgumentParser(
            description='Automatically organize your messy folders',
            epilog='Example: onefile --src ~/Downloads --watch --interval 300'
        )
        
        # Main arguments
        parser.add_argument(
            '--src',
            type=str,
            required=True,
            help='Source directory to organize'
        )
        
        # Modes
        mode_group = parser.add_mutually_exclusive_group(required=True)
        mode_group.add_argument(
            '--once',
            action='store_true',
            help='Run organization once and exit'
        )
        mode_group.add_argument(
            '--watch',
            action='store_true',
            help='Run in watch mode (daemon)'
        )
        
        # Watch options
        watch_group = parser.add_argument_group('Watch options')
        watch_group.add_argument(
            '--interval',
            type=int,
            default=300,
            help='Interval between checks in seconds (default: 300)'
        )
        
        # Filter options
        filter_group = parser.add_argument_group('Filter options')
        filter_group.add_argument(
            '--min-size',
            type=self._parse_size,
            help='Minimum file size (e.g., 1K, 1M, 1G)'
        )
        filter_group.add_argument(
            '--max-size',
            type=self._parse_size,
            help='Maximum file size (e.g., 1K, 1M, 1G)'
        )
        filter_group.add_argument(
            '--min-age',
            type=int,
            help='Minimum file age in days'
        )
        filter_group.add_argument(
            '--max-age',
            type=int,
            help='Maximum file age in days'
        )
        filter_group.add_argument(
            '--no-hidden',
            action='store_true',
            help='Skip hidden files and directories'
        )
        filter_group.add_argument(
            '--no-system',
            action='store_true',
            help='Skip system files (Windows only)'
        )
        
        # Behavior options
        behavior_group = parser.add_argument_group('Behavior options')
        behavior_group.add_argument(
            '--use-ctime',
            action='store_true',
            help='Use creation time instead of modification time for age checks'
        )
        behavior_group.add_argument(
            '--dry-run',
            action='store_true',
            help='Simulate file operations without making changes'
        )
        behavior_group.add_argument(
            '--config',
            type=str,
            help='Path to JSON config file'
        )
        
        # Output options
        output_group = parser.add_argument_group('Output options')
        output_group.add_argument(
            '-v', '--verbose',
            action='store_true',
            help='Enable verbose output'
        )
        output_group.add_argument(
            '-q', '--quiet',
            action='store_true',
            help='Only show errors'
        )
        output_group.add_argument(
            '--json',
            action='store_true',
            help='Output results as JSON'
        )
        
        return parser
    
    def _parse_size(self, size_str: str) -> int:
        """Parse size string with units (e.g., 1K, 2M, 3G) to bytes."""
        size_str = size_str.upper()
        if size_str.endswith('K'):
            return int(size_str[:-1]) * 1024
        elif size_str.endswith('M'):
            return int(size_str[:-1]) * 1024 * 1024
        elif size_str.endswith('G'):
            return int(size_str[:-1]) * 1024 * 1024 * 1024
        else:
            return int(size_str)
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from a JSON file."""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading config file: {e}")
            return {}
    
    def _get_organizer_kwargs(self, args: argparse.Namespace) -> Dict[str, Any]:
        """Get keyword arguments for the FileOrganizer."""
        kwargs = {
            'min_size': args.min_size,
            'max_size': args.max_size,
            'min_age_days': args.min_age,
            'max_age_days': args.max_age,
            'ignore_hidden': args.no_hidden,
            'ignore_system': args.no_system,
            'use_modified_time': not args.use_ctime,
            'dry_run': args.dry_run,
        }
        
        # Load additional config from file if specified
        if args.config:
            config = self._load_config(args.config)
            if 'custom_rules' in config:
                kwargs['custom_rules'] = config['custom_rules']
        
        return kwargs
    
    def _setup_logging(self, args: argparse.Namespace) -> None:
        """Configure logging based on verbosity level."""
        if args.quiet:
            logging.getLogger().setLevel(logging.ERROR)
        elif args.verbose:
            logging.getLogger().setLevel(logging.DEBUG)
        else:
            logging.getLogger().setLevel(logging.INFO)
    
    def run(self, args: Optional[List[str]] = None) -> int:
        """Run the CLI with the given arguments."""
        # Parse arguments
        parsed_args = self.parser.parse_args(args)
        
        # Set up logging
        self._setup_logging(parsed_args)
        
        # Get organizer arguments
        organizer_kwargs = self._get_organizer_kwargs(parsed_args)
        
        try:
            # Run in the appropriate mode
            if parsed_args.once:
                return self._run_once(parsed_args.src, organizer_kwargs, parsed_args.json)
            elif parsed_args.watch:
                return self._run_watch(parsed_args.src, parsed_args.interval, organizer_kwargs)
            
            # Shouldn't reach here due to required mutually exclusive group
            self.parser.print_help()
            return 1
            
        except Exception as e:
            logger.error(f"Error: {e}", exc_info=parsed_args.verbose)
            return 1
    
    def _run_once(self, src_dir: str, organizer_kwargs: Dict[str, Any], output_json: bool) -> int:
        """Run organization once and exit."""
        logger.info(f"Organizing {src_dir}...")
        
        try:
            stats = organize_folder(src_dir, **organizer_kwargs)
            
            if output_json:
                print(json.dumps(stats, indent=2))
            else:
                logger.info(
                    f"Organization complete. "
                    f"Processed: {stats['processed']}, "
                    f"Moved: {stats['moved']}, "
                    f"Skipped: {stats['skipped']}, "
                    f"Errors: {stats['errors']}, "
                    f"Time: {stats['elapsed_seconds']:.2f}s"
                )
            
            return 0 if stats['errors'] == 0 else 1
            
        except Exception as e:
            logger.error(f"Error during organization: {e}", exc_info=True)
            return 1
    
    def _run_watch(self, src_dir: str, interval: int, organizer_kwargs: Dict[str, Any]) -> int:
        """Run in watch mode (daemon)."""
        try:
            logger.info(f"Starting watcher for {src_dir} (interval: {interval}s)")
            logger.info("Press Ctrl+C to stop")
            
            run_daemon(
                source_dir=src_dir,
                interval=interval,
                **organizer_kwargs
            )
            
            return 0
            
        except KeyboardInterrupt:
            logger.info("Watcher stopped by user")
            return 0
        except Exception as e:
            logger.error(f"Error in watcher: {e}", exc_info=True)
            return 1

def main(args: Optional[List[str]] = None) -> int:
    """Entry point for the CLI."""
    cli = OneFileCLI()
    return cli.run(args)

if __name__ == "__main__":
    sys.exit(main())
