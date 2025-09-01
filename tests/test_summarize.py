import io
import logging
from typing import Dict
import asyncio
import pytest
import httpx

logger = logging.getLogger("TestSummarizationEndpoint")
TIMEOUT = 120  # seconds
TASK_TIMEOUT = 240 # seconds
SERVICE_URL = "http://localhost:8000/summarize"

class TestSummarizationEndpoint:
    def assert_communication_successful(self, response: httpx.Response) -> Dict:
        result = response.content
        logger.info(f"Got result {result}")
        assert response.status_code == 200, (
            f"Unexpected status code: {response.status_code}. Message: {result}"
        )
        return response.json()


    @pytest.mark.asyncio
    async def test_summarization_endpoint(self, docker_services):
        """Test POST /query with real audio and real services."""
        with open("tests/resources/test.wav", "rb") as f:
            audio_bytes = f.read()
        async with httpx.AsyncClient(base_url=SERVICE_URL, timeout=TIMEOUT) as client:
            response = await client.post(
                "/query",
                files={"file": ("test.wav", io.BytesIO(audio_bytes), "audio/wav")},
            )
        result = self.assert_communication_successful(response)

        assert "id" in result
        assert result["status"] in ("PENDING", "STARTED", "SUCCESS")

    @pytest.mark.asyncio
    async def test_result_endpoint(self, docker_services):
        """Test GET /result returns status and result after submitting audio."""
        with open("tests/resources/test.wav", "rb") as f:
            audio_bytes = f.read()
        async with httpx.AsyncClient(base_url=SERVICE_URL, timeout=TIMEOUT) as client:
            post_response = await client.post(
                "/query",
                files={"file": ("test.wav", io.BytesIO(audio_bytes), "audio/wav")},
            )
            post_result = self.assert_communication_successful(post_response)
            task_id = post_result["id"]

            # Poll the task until it succeeds or fails
            for _ in range(TASK_TIMEOUT):
                get_response = await client.get(f"/result?task_id={task_id}")
                get_result = self.assert_communication_successful(get_response)
                if get_result["status"] in ("SUCCESS", "FAILURE"):
                    break
                await asyncio.sleep(2)

        assert get_result["status"] in ("SUCCESS", "FAILURE")
        assert "result" in get_result

    @pytest.mark.asyncio
    async def test_export_pdf(self, docker_services):
        """Test PDF export endpoint with a completed task."""
        with open("tests/resources/test.wav", "rb") as f:
            audio_bytes = f.read()
        async with httpx.AsyncClient(base_url=SERVICE_URL, timeout=TIMEOUT) as client:
            post_response = await client.post(
                "/query",
                files={"file": ("test.wav", io.BytesIO(audio_bytes), "audio/wav")},
            )
            post_result = self.assert_communication_successful(post_response)
            task_id = post_result["id"]

            # Wait for task completion
            for _ in range(TASK_TIMEOUT):
                result_response = await client.get(f"/result?task_id={task_id}")
                result_data = self.assert_communication_successful(result_response)
                if result_data["status"] == "SUCCESS":
                    break
                await asyncio.sleep(2)

            # Export PDF
            pdf_response = await client.get(f"/export/pdf?task_id={task_id}&filename=test_output")
        assert pdf_response.status_code == 200
        assert pdf_response.headers["content-type"] == "application/pdf"