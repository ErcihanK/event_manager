import pytest
from app.utils.template_manager import TemplateManager
import os
from pathlib import Path

@pytest.fixture
def template_manager():
    return TemplateManager()

@pytest.fixture
def temp_template_dir(tmp_path):
    # Create temporary template files
    templates = {
        'header.md': '# Header',
        'footer.md': '## Footer',
        'test.md': 'Hello {{name}}!',
        'test.html': '<p>Hello {{name}}!</p>',
        'email_verification.html': '<p>Verify at {{verification_url}}</p>'
    }
    
    for name, content in templates.items():
        (tmp_path / name).write_text(content)
    
    return tmp_path

def test_init(template_manager):
    assert isinstance(template_manager, TemplateManager)
    assert template_manager.templates_dir.exists()

def test_read_template(template_manager, monkeypatch, temp_template_dir):
    monkeypatch.setattr(template_manager, 'template_dir', str(temp_template_dir))
    content = template_manager._read_template('test.html')
    assert 'Hello' in content

def test_apply_email_styles(template_manager):
    html = "<h1>Test</h1><p>Content</p><a href='#'>Link</a>"
    styled = template_manager._apply_email_styles(html)
    assert 'style=' in styled
    assert 'font-family' in styled
    assert 'color' in styled

def test_render_template(template_manager, monkeypatch, temp_template_dir):
    monkeypatch.setattr(template_manager, 'template_dir', str(temp_template_dir))
    result = template_manager.render_template('test', name='John')
    assert 'John' in result
    assert 'style=' in result

def test_render_email_template(template_manager, monkeypatch, temp_template_dir):
    monkeypatch.setattr(template_manager, 'template_dir', str(temp_template_dir))
    result = template_manager.render_email_template('email_verification', 
                                                  {'verification_url': 'http://test.com'})
    assert 'http://test.com' in result

def test_template_not_found(template_manager):
    with pytest.raises(ValueError):
        template_manager._read_template('non_existent.html')

def test_create_default_templates(template_manager, tmp_path, monkeypatch):
    monkeypatch.setattr(template_manager, 'template_dir', str(tmp_path))
    template_manager._create_default_templates()
    assert (Path(tmp_path) / 'email_verification.html').exists()
    assert (Path(tmp_path) / 'verification_email.md').exists()
