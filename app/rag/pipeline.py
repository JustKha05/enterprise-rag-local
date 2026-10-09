from dataclasses import dataclass
from time import perf_counter

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_ollama import ChatOllama

from app.rag.prompts import SYSTEM_PROMPT, build_user_prompt

from app.config import settings
from app.retrieval.retriever import (
    DocumentRetriever,
    RetrievalResult,
)

@dataclass(frozen=True)
class RAGResponse:
    answer: str
    sources: list[RetrievalResult]
    retrieval_seconds: float
    generation_seconds: float
    done_reason: str | None


class RAGPipeline:
    def __init__(self, model_name: str | None = None) -> None:
        self.model_name = (
            model_name
            if model_name is not None
            else settings.generation_model
        ).strip()

        if not self.model_name:
            raise ValueError("Model name must not be empty")

        self.retriever = DocumentRetriever()

        model_family = self.model_name.split(":")[0]
        model_options = {}
        output_limit = 400

        if model_family in {"qwen3", "gemma4"}:
            model_options["reasoning"] = False

        elif model_family == "deepseek-r1":
            model_options["reasoning"] = True
            output_limit = 1200

        self.llm = ChatOllama(
            model=self.model_name,
            base_url=settings.ollama_url,
            temperature=0,
            num_ctx=4096,
            num_predict=output_limit,
            keep_alive="5m",
            client_kwargs={"timeout": 600.0},
            **model_options,
        )

    def ask(self, query: str, top_k: int = 3) -> RAGResponse:
        retrieval_start = perf_counter()

        results = self.retriever.retrieve(
            query=query,
            top_k=top_k,
        )

        retrieval_seconds = perf_counter() - retrieval_start

        if not results:
            return RAGResponse(
                answer=(
                    "No matching document chunks were retrieved. "
                    "There is not enough evidence to answer."
                ),
                sources=[],
                retrieval_seconds=retrieval_seconds,
                generation_seconds=0.0,
                done_reason=None,
            )

        sources = [
            {
                "label": f"S{index}",
                "page_content": result.document.page_content,
                "metadata": result.document.metadata,
            }
            for index, result in enumerate(results, start=1)
        ]

        user_prompt = build_user_prompt(query, sources)

        generation_start = perf_counter()

        message = self.llm.invoke(
            [
                SystemMessage(content=SYSTEM_PROMPT),
                HumanMessage(content=user_prompt),
            ]
        )

        generation_seconds = perf_counter() - generation_start

        if not isinstance(message.content, str):
            raise TypeError("Expected a text response from the model")

        return RAGResponse(
            answer=message.content.strip(),
            sources=results,
            retrieval_seconds=retrieval_seconds,
            generation_seconds=generation_seconds,
            done_reason=message.response_metadata.get("done_reason"),
        )

    def close(self) -> None:
        self.retriever.close()