#!/usr/bin/env python3
"""
Simple test of Yuho v4 without external dependencies
"""

import sys
import os

# Test basic AST nodes
sys.path.insert(0, os.path.dirname(__file__))

try:
    from ast_nodes import *
    print("✓ AST nodes imported successfully")

    # Test creating basic nodes
    program = Program(statements=[])
    print("✓ Can create Program node")

    literal = Literal(value=42, literal_type=YuhoType.INT)
    print("✓ Can create Literal node")

    struct_def = StructDefinition(name="TestStruct", members=[])
    print("✓ Can create StructDefinition node")

    print("\\n✓ All basic AST functionality works!")

except ImportError as e:
    print(f"✗ Import error: {e}")
except Exception as e:
    print(f"✗ Error: {e}")

# Test basic file operations
try:
    test_yuho_code = '''
struct Cheating {
    accused: string,
    victim: string,
    harm: bool,
}
'''

    with open('test_example.yh', 'w') as f:
        f.write(test_yuho_code)

    print("✓ Can write Yuho files")

    with open('test_example.yh', 'r') as f:
        content = f.read()

    print("✓ Can read Yuho files")
    print(f"  Content: {len(content)} characters")

    # Clean up
    os.remove('test_example.yh')
    print("✓ File operations complete")

except Exception as e:
    print(f"✗ File operation error: {e}")

print("\\nYuho v4.0 basic structure is ready!")
print("To use full functionality, install dependencies:")
print("  pip install lark-parser click colorama")