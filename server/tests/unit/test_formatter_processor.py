import pytest
from services.processors.formatter import FormatterProcessor
from errors import ProcessingError


class TestFormatterProcessor:
    """Test cases for FormatterProcessor"""

    def setup_method(self):
        """Set up test fixtures"""
        self.processor = FormatterProcessor()

    @pytest.mark.asyncio
    async def test_process_uppercase(self):
        """Test uppercase formatting"""
        input_data = "hello world"
        config = {"format_type": "uppercase"}

        result = await self.processor.process(input_data, config)

        assert result == "HELLO WORLD"

    @pytest.mark.asyncio
    async def test_process_lowercase(self):
        """Test lowercase formatting"""
        input_data = "HELLO WORLD"
        config = {"format_type": "lowercase"}

        result = await self.processor.process(input_data, config)

        assert result == "hello world"

    @pytest.mark.asyncio
    async def test_process_trim(self):
        """Test trim formatting"""
        input_data = "  hello world  \n\t"
        config = {"format_type": "trim"}

        result = await self.processor.process(input_data, config)

        assert result == "hello world"

    @pytest.mark.asyncio
    async def test_process_replace(self):
        """Test replace formatting"""
        input_data = "hello world hello"
        config = {
            "format_type": "replace",
            "find": "hello",
            "replace_with": "hi"
        }

        result = await self.processor.process(input_data, config)

        assert result == "hi world hi"

    @pytest.mark.asyncio
    async def test_process_replace_empty_find(self):
        """Test replace formatting with empty find string"""
        input_data = "hello world"
        config = {
            "format_type": "replace",
            "find": "",
            "replace_with": "X"
        }

        result = await self.processor.process(input_data, config)

        # Empty string replacement replaces between every character
        assert result == "XhXeXlXlXoX XwXoXrXlXdX"

    @pytest.mark.asyncio
    async def test_process_replace_empty_replace_with(self):
        """Test replace formatting with empty replace_with string"""
        input_data = "hello world hello"
        config = {
            "format_type": "replace",
            "find": "hello",
            "replace_with": ""
        }

        result = await self.processor.process(input_data, config)

        assert result == " world "

    @pytest.mark.asyncio
    async def test_process_invalid_format_type(self):
        """Test processing with invalid format_type"""
        input_data = "hello world"
        config = {"format_type": "invalid_format"}

        with pytest.raises(ProcessingError) as exc_info:
            await self.processor.process(input_data, config)

        assert "Formatter configuration is invalid" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_process_missing_format_type(self):
        """Test processing with missing format_type"""
        input_data = "hello world"
        config = {}

        with pytest.raises(ProcessingError):
            await self.processor.process(input_data, config)

    @pytest.mark.asyncio
    async def test_process_replace_missing_find(self):
        """Test replace processing without find parameter"""
        input_data = "hello world"
        config = {
            "format_type": "replace",
            "replace_with": "hi"
        }

        result = await self.processor.process(input_data, config)

        # Should default to empty string for find (replaces between every character)
        assert result == "hihhiehilhilhiohi hiwhiohirhilhidhi"

    @pytest.mark.asyncio
    async def test_process_replace_missing_replace_with(self):
        """Test replace processing without replace_with parameter"""
        input_data = "hello world"
        config = {
            "format_type": "replace",
            "find": "hello"
        }

        result = await self.processor.process(input_data, config)

        # Should default to empty string for replace_with
        assert result == " world"

    def test_validate_config_valid_uppercase(self):
        """Test config validation for uppercase format"""
        config = {"format_type": "uppercase"}

        # Should not raise any exception
        self.processor.validate_config(config)

    def test_validate_config_valid_lowercase(self):
        """Test config validation for lowercase format"""
        config = {"format_type": "lowercase"}

        # Should not raise any exception
        self.processor.validate_config(config)

    def test_validate_config_valid_trim(self):
        """Test config validation for trim format"""
        config = {"format_type": "trim"}

        # Should not raise any exception
        self.processor.validate_config(config)

    def test_validate_config_valid_replace(self):
        """Test config validation for replace format with all parameters"""
        config = {
            "format_type": "replace",
            "find": "hello",
            "replace_with": "hi"
        }

        # Should not raise any exception
        self.processor.validate_config(config)

    def test_validate_config_missing_format_type(self):
        """Test config validation without format_type"""
        config = {}

        with pytest.raises(ValueError) as exc_info:
            self.processor.validate_config(config)

        assert "format_type is required" in str(exc_info.value)

    def test_validate_config_invalid_format_type(self):
        """Test config validation with invalid format_type"""
        config = {"format_type": "invalid"}

        with pytest.raises(ValueError) as exc_info:
            self.processor.validate_config(config)

        assert "format_type must be one of" in str(exc_info.value)

    def test_validate_config_replace_missing_find(self):
        """Test config validation for replace without find parameter"""
        config = {
            "format_type": "replace",
            "replace_with": "hi"
        }

        with pytest.raises(ValueError) as exc_info:
            self.processor.validate_config(config)

        assert "find is required when format_type is 'replace'" in str(exc_info.value)

    def test_validate_config_replace_missing_replace_with(self):
        """Test config validation for replace without replace_with parameter"""
        config = {
            "format_type": "replace",
            "find": "hello"
        }

        with pytest.raises(ValueError) as exc_info:
            self.processor.validate_config(config)

        assert "replace_with is required when format_type is 'replace'" in str(exc_info.value)

    def test_get_required_config_keys(self):
        """Test required configuration keys"""
        keys = self.processor.get_required_config_keys()

        assert keys == ["format_type"]