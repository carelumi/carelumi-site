GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


def get_llm_response(document_text: str) -> schema.LanguageModelResponse:
    client = OpenAI(
        api_key=GEMINI_API_KEY,
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
    )

    completion = client.beta.chat.completions.parse(
        model="gemini-2.0-flash",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": document_text},
        ],
        response_format=schema.LanguageModelResponse,
    )

    return completion.choices[0].message.parsed
