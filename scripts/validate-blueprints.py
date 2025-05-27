#!/usr/bin/env python3
"""
Authentik Blueprint Validation Script

This script validates the syntax and structure of Authentik blueprints
before they are applied to the Authentik instance.
"""

import os
import sys
import yaml
import json
from pathlib import Path
from typing import Dict, List, Any, Optional

def validate_yaml_syntax(file_path: Path) -> tuple[bool, Optional[str]]:
    """Validate YAML syntax of a blueprint file."""
    try:
        with open(file_path, 'r') as f:
            yaml.safe_load(f)
        return True, None
    except yaml.YAMLError as e:
        return False, str(e)
    except Exception as e:
        return False, f"Error reading file: {str(e)}"

def validate_blueprint_structure(blueprint: Dict[str, Any], file_path: Path) -> List[str]:
    """Validate the structure of an Authentik blueprint."""
    errors = []
    
    # Check required top-level keys
    required_keys = ['version', 'metadata', 'entries']
    for key in required_keys:
        if key not in blueprint:
            errors.append(f"Missing required key: {key}")
    
    # Validate version
    if 'version' in blueprint:
        if not isinstance(blueprint['version'], int) or blueprint['version'] != 1:
            errors.append("Version must be 1")
    
    # Validate metadata
    if 'metadata' in blueprint:
        if not isinstance(blueprint['metadata'], dict):
            errors.append("Metadata must be a dictionary")
        elif 'name' not in blueprint['metadata']:
            errors.append("Metadata must contain 'name' field")
    
    # Validate entries
    if 'entries' in blueprint:
        if not isinstance(blueprint['entries'], list):
            errors.append("Entries must be a list")
        else:
            for i, entry in enumerate(blueprint['entries']):
                entry_errors = validate_entry(entry, i)
                errors.extend(entry_errors)
    
    return errors

def validate_entry(entry: Dict[str, Any], index: int) -> List[str]:
    """Validate a single blueprint entry."""
    errors = []
    entry_prefix = f"Entry {index}"
    
    # Check required entry keys
    required_keys = ['model', 'identifiers', 'attrs']
    for key in required_keys:
        if key not in entry:
            errors.append(f"{entry_prefix}: Missing required key: {key}")
    
    # Validate model format
    if 'model' in entry:
        model = entry['model']
        if not isinstance(model, str) or '.' not in model:
            errors.append(f"{entry_prefix}: Model must be in format 'app.model'")
    
    # Validate identifiers
    if 'identifiers' in entry:
        if not isinstance(entry['identifiers'], dict):
            errors.append(f"{entry_prefix}: Identifiers must be a dictionary")
    
    # Validate attrs
    if 'attrs' in entry:
        if not isinstance(entry['attrs'], dict):
            errors.append(f"{entry_prefix}: Attrs must be a dictionary")
    
    return errors

def validate_oauth2_provider(entry: Dict[str, Any]) -> List[str]:
    """Validate OAuth2 provider specific fields."""
    errors = []
    
    if entry.get('model') == 'authentik_providers_oauth2.oauth2provider':
        attrs = entry.get('attrs', {})
        
        # Check required OAuth2 fields
        required_fields = ['name', 'client_type', 'authorization_grant_type']
        for field in required_fields:
            if field not in attrs:
                errors.append(f"OAuth2 Provider missing required field: {field}")
        
        # Validate client_type
        if 'client_type' in attrs:
            valid_types = ['confidential', 'public']
            if attrs['client_type'] not in valid_types:
                errors.append(f"Invalid client_type: {attrs['client_type']}. Must be one of: {valid_types}")
        
        # Validate authorization_grant_type
        if 'authorization_grant_type' in attrs:
            valid_grants = ['authorization-code', 'client-credentials', 'implicit']
            if attrs['authorization_grant_type'] not in valid_grants:
                errors.append(f"Invalid authorization_grant_type: {attrs['authorization_grant_type']}")
    
    return errors

def validate_application(entry: Dict[str, Any]) -> List[str]:
    """Validate application specific fields."""
    errors = []
    
    if entry.get('model') == 'authentik_core.application':
        attrs = entry.get('attrs', {})
        
        # Check required application fields
        required_fields = ['name', 'slug']
        for field in required_fields:
            if field not in attrs:
                errors.append(f"Application missing required field: {field}")
        
        # Validate slug format (should be URL-safe)
        if 'slug' in attrs:
            slug = attrs['slug']
            if not slug.islower() or not slug.replace('-', '').replace('_', '').isalnum():
                errors.append(f"Invalid slug format: {slug}. Should be lowercase alphanumeric with hyphens/underscores")
    
    return errors

def validate_blueprint_file(file_path: Path) -> Dict[str, Any]:
    """Validate a single blueprint file and return results."""
    result = {
        'file': str(file_path),
        'valid': True,
        'errors': [],
        'warnings': []
    }
    
    # Check if file exists
    if not file_path.exists():
        result['valid'] = False
        result['errors'].append("File does not exist")
        return result
    
    # Validate YAML syntax
    yaml_valid, yaml_error = validate_yaml_syntax(file_path)
    if not yaml_valid:
        result['valid'] = False
        result['errors'].append(f"YAML syntax error: {yaml_error}")
        return result
    
    # Load and validate blueprint structure
    try:
        with open(file_path, 'r') as f:
            blueprint = yaml.safe_load(f)
        
        # Validate blueprint structure
        structure_errors = validate_blueprint_structure(blueprint, file_path)
        result['errors'].extend(structure_errors)
        
        # Validate specific entry types
        if 'entries' in blueprint:
            for entry in blueprint['entries']:
                # OAuth2 provider validation
                oauth2_errors = validate_oauth2_provider(entry)
                result['errors'].extend(oauth2_errors)
                
                # Application validation
                app_errors = validate_application(entry)
                result['errors'].extend(app_errors)
        
        if result['errors']:
            result['valid'] = False
    
    except Exception as e:
        result['valid'] = False
        result['errors'].append(f"Unexpected error: {str(e)}")
    
    return result

def main():
    """Main validation function."""
    print("🔍 Validating Authentik blueprints...")
    
    # Find blueprint directory
    blueprint_dir = Path("config/authentik/blueprints")
    if not blueprint_dir.exists():
        print(f"❌ Blueprint directory not found: {blueprint_dir}")
        sys.exit(1)
    
    # Find all YAML files in blueprints directory
    blueprint_files = list(blueprint_dir.glob("*.yaml")) + list(blueprint_dir.glob("*.yml"))
    
    if not blueprint_files:
        print("⚠️  No blueprint files found")
        return
    
    print(f"Found {len(blueprint_files)} blueprint files")
    
    all_valid = True
    results = []
    
    # Validate each blueprint file
    for file_path in sorted(blueprint_files):
        print(f"\n📄 Validating {file_path.name}...")
        result = validate_blueprint_file(file_path)
        results.append(result)
        
        if result['valid']:
            print(f"✅ {file_path.name} is valid")
        else:
            print(f"❌ {file_path.name} has errors:")
            for error in result['errors']:
                print(f"   - {error}")
            all_valid = False
        
        if result['warnings']:
            print(f"⚠️  {file_path.name} warnings:")
            for warning in result['warnings']:
                print(f"   - {warning}")
    
    # Generate validation report
    report = {
        'validation_timestamp': None,
        'total_files': len(blueprint_files),
        'valid_files': sum(1 for r in results if r['valid']),
        'invalid_files': sum(1 for r in results if not r['valid']),
        'results': results
    }
    
    # Save report
    report_path = Path("config/authentik/blueprint-validation-report.json")
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📊 Validation Report:")
    print(f"   Total files: {report['total_files']}")
    print(f"   Valid files: {report['valid_files']}")
    print(f"   Invalid files: {report['invalid_files']}")
    print(f"   Report saved to: {report_path}")
    
    if all_valid:
        print("\n🎉 All blueprint files are valid!")
        sys.exit(0)
    else:
        print("\n❌ Some blueprint files have errors. Please fix them before applying.")
        sys.exit(1)

if __name__ == "__main__":
    main()
