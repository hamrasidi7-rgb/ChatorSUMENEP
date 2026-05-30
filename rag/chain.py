from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableParallel
from langchain_core.documents import Document
from typing import List

from rag.vectorstore import get_vectorstore
from config.settings import get_settings

SYSTEM_PROMPT = """Anda adalah Asisten Informasi Resmi Pemerintah Kabupaten Sumenep.
Tugas Anda adalah menjawab pertanyaan masyarakat mengenai pelayanan publik, program pemerintah, \
kebijakan, capaian kinerja, dan informasi umum Kabupaten Sumenep secara akurat dan ramah.

Panduan menjawab:
- Gunakan Bahasa Indonesia yang baik, sopan, dan mudah dipahami.
- Jawab HANYA berdasarkan konteks dokumen yang diberikan di bawah ini.
- Jika informasi tidak tersedia dalam konteks, katakan dengan jujur bahwa Anda belum memiliki \
  informasi tersebut dan arahkan masyarakat untuk menghubungi OPD terkait atau mengunjungi \
  website resmi Pemkab Sumenep di sumenepkab.go.id.
- Jangan mengarang atau menambah informasi di luar konteks.
- Sertakan nama dokumen/sumber jika relevan agar masyarakat dapat merujuk lebih lanjut.

Konteks Dokumen:
{context}
"""

HUMAN_PROMPT = "{question}"


def _format_docs(docs: List[Document]) -> str:
    parts = []
    for i, doc in enumerate(docs, 1):
        source = doc.metadata.get("source", "Dokumen tidak diketahui")
        parts.append(f"[{i}] Sumber: {source}\n{doc.page_content}")
    return "\n\n---\n\n".join(parts)


def build_rag_chain():
    settings = get_settings()

    llm = ChatGroq(
        api_key=settings.groq_api_key,
        model=settings.groq_model,
        temperature=0.1,
        max_tokens=1024,
    )

    vectorstore = get_vectorstore()
    retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": settings.retriever_top_k},
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("human", HUMAN_PROMPT),
    ])

    rag_chain = (
        RunnableParallel(
            context=retriever | _format_docs,
            question=RunnablePassthrough(),
        )
        | prompt
        | llm
        | StrOutputParser()
    )

    return rag_chain


# Singleton chain — di-build sekali saat startup
_chain = None


def get_chain():
    global _chain
    if _chain is None:
        _chain = build_rag_chain()
    return _chain


async def ask(question: str) -> str:
    chain = get_chain()
    return await chain.ainvoke(question)
