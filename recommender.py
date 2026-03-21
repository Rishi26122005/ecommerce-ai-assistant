# # """
# # Product Recommender Engine
# # Hybrid BM25 + FAISS Vector Search + Gemini LLM
# # Ported from the Jupyter Notebook NLP project
# # """

# # import re
# # import json
# # import math
# # import numpy as np
# # import pandas as pd

# # # ─── Lazy imports (heavy libs) ────────────────────────────────────────────────
# # _faiss = None
# # _SentenceTransformer = None
# # _BM25Okapi = None
# # _genai = None


# # def _load_libs():
# #     global _faiss, _SentenceTransformer, _BM25Okapi, _genai
# #     if _faiss is None:
# #         import faiss
# #         _faiss = faiss
# #     if _SentenceTransformer is None:
# #         from sentence_transformers import SentenceTransformer
# #         _SentenceTransformer = SentenceTransformer
# #     if _BM25Okapi is None:
# #         from rank_bm25 import BM25Okapi
# #         _BM25Okapi = BM25Okapi
# #     if _genai is None:
# #         from google import genai
# #         _genai = genai


# # # ─── Price Cleaner ────────────────────────────────────────────────────────────
# # def _clean_price(x):
# #     if isinstance(x, str):
# #         x = re.sub(r"[₹$,]", "", x).strip()
# #         try:
# #             return float(x)
# #         except ValueError:
# #             return None
# #     return x


# # # ─── Text Combiner ────────────────────────────────────────────────────────────
# # def _combine_text(row):
# #     return (
# #         f"Product Name: {row.get('product_name', '')}\n"
# #         f"Category: {row.get('category', '')}\n"
# #         f"Description: {row.get('about_product', '')}\n"
# #         f"Review Title: {row.get('review_title', '')}\n"
# #         f"Review Content: {row.get('review_content', '')}"
# #     )


# # # ─── Main Class ───────────────────────────────────────────────────────────────
# # class ProductRecommender:

# #     def __init__(self, dataset_path: str, gemini_api_key: str):
# #         print("🔄 Loading dataset …")
# #         self.df = self._load_dataset(dataset_path)
# #         self.gemini_api_key = gemini_api_key
# #         self._bm25 = None
# #         self._index = None
# #         self._embeddings = None
# #         self._embedding_model = None
# #         self._gemini_client = None
# #         self._ready = False

# #         try:
# #             _load_libs()
# #             self._build_index()
# #             self._init_gemini()
# #             self._ready = True
# #             print("✅ Recommender ready.")
# #         except Exception as e:
# #             print(f"⚠️  Recommender init error (running in limited mode): {e}")

# #     # ── Data Loading ──────────────────────────────────────────────────────────
# #     def _load_dataset(self, path: str) -> pd.DataFrame:
# #         df = pd.read_csv(path)
# #         df["discounted_price"] = df["discounted_price"].apply(_clean_price)
# #         df["actual_price"]     = df["actual_price"].apply(_clean_price)
# #         df["rating"]           = pd.to_numeric(df["rating"], errors="coerce")
# #         df["rating_count"]     = df["rating_count"].astype(str).str.replace(",", "")
# #         df["rating_count"]     = pd.to_numeric(df["rating_count"], errors="coerce")
# #         df["discount_percentage"] = df["discount_percentage"].astype(str).str.replace("%", "")
# #         df["discount_percentage"] = pd.to_numeric(df["discount_percentage"], errors="coerce")
# #         df = df.dropna(subset=["product_name", "about_product"])
# #         df = df.reset_index(drop=True)
# #         # Clean category to top-level only
# #         df["top_category"] = df["category"].astype(str).apply(
# #             lambda x: x.split("|")[0].strip()
# #         )
# #         df["combined_text"] = df.apply(_combine_text, axis=1)
# #         return df

# #     # ── Index Building ────────────────────────────────────────────────────────
# #     def _build_index(self):
# #         print("🔄 Building BM25 index …")
# #         corpus = self.df["combined_text"].tolist()
# #         tokenized = [doc.lower().split() for doc in corpus]
# #         self._bm25 = _BM25Okapi(tokenized)

# #         print("🔄 Encoding embeddings (this may take a while) …")
# #         self._embedding_model = _SentenceTransformer("all-MiniLM-L6-v2")
# #         self._embeddings = self._embedding_model.encode(corpus, show_progress_bar=True)

# #         dim = self._embeddings.shape[1]
# #         self._index = _faiss.IndexFlatL2(dim)
# #         self._index.add(np.array(self._embeddings).astype("float32"))
# #         print(f"✅ FAISS index: {self._index.ntotal} vectors")

# #     def _init_gemini(self):
# #         if self.gemini_api_key and self.gemini_api_key != "YOUR_GEMINI_API_KEY_HERE":
# #             self._gemini_client = _genai.Client(api_key=self.gemini_api_key)
# #             print("✅ Gemini client initialized.")

# #     # ── Hybrid Retrieval ──────────────────────────────────────────────────────
# #     def _hybrid_retrieval(self, query: str, top_k: int = 5) -> pd.DataFrame:
# #         # BM25 scores
# #         tokenized_query = query.lower().split()
# #         bm25_scores = self._bm25.get_scores(tokenized_query)

# #         # Vector search
# #         q_emb = self._embedding_model.encode([query])
# #         D, I  = self._index.search(np.array(q_emb).astype("float32"), top_k)

# #         # Normalize BM25
# #         bm25_norm = (bm25_scores - bm25_scores.min()) / (bm25_scores.max() + 1e-9)

# #         # Combine scores
# #         scores = {}
# #         for idx in I[0]:
# #             scores[idx] = 0.6 + 0.4 * bm25_norm[idx]

# #         for i, idx in enumerate(I[0]):
# #             faiss_score = 1 / (1 + D[0][i])  # distance → similarity
# #             scores[idx] = scores.get(idx, 0) * faiss_score

# #         top_indices = sorted(scores, key=scores.get, reverse=True)[:top_k]
# #         return self.df.iloc[top_indices].copy()

# #     # ── Build Context for LLM ─────────────────────────────────────────────────
# #     def _build_context(self, products_df: pd.DataFrame) -> str:
# #         ctx = ""
# #         for _, row in products_df.iterrows():
# #             ctx += (
# #                 f"\nProduct Name: {row['product_name']}\n"
# #                 f"Price: ₹{row.get('discounted_price', 'N/A')}\n"
# #                 f"Rating: {row.get('rating', 'N/A')}/5\n"
# #                 f"Category: {row.get('category', 'N/A')}\n"
# #                 f"Description: {row.get('about_product', '')[:300]}\n"
# #                 f"Top Review: {str(row.get('review_content', ''))[:200]}\n\n"
# #             )
# #         return ctx

# #     # ── Gemini LLM Call ───────────────────────────────────────────────────────
# #     def _call_gemini(self, prompt: str) -> str:
# #         if not self._gemini_client:
# #             return "⚠️ AI recommendation unavailable. Please configure a valid Gemini API key."
# #         response = self._gemini_client.models.generate_content(
# #             model="gemini-2.5-flash",
# #             contents=prompt,
# #         )
# #         return response.text

# #     # ── Public: Recommend ─────────────────────────────────────────────────────
# #     def recommend(self, query: str, top_k: int = 5):
# #         """Returns (ai_response_text, list_of_product_dicts)"""
# #         if not self._ready:
# #             return "Recommender is not initialized.", []

# #         retrieved = self._hybrid_retrieval(query, top_k=top_k)
# #         context   = self._build_context(retrieved)

# #         prompt = (
# #             "You are an intelligent e-commerce recommendation assistant.\n\n"
# #             f"User Query:\n{query}\n\n"
# #             "Based on the following products, recommend the best products.\n"
# #             "Show pros and cons of the products in brief.\n"
# #             "Explain why each product is suitable based on reviews and ratings.\n"
# #             "Format your response with clear sections for each product.\n\n"
# #             f"Products:\n{context}"
# #         )

# #         ai_response = self._call_gemini(prompt)
# #         products    = self._rows_to_dicts(retrieved)
# #         return ai_response, products

# #     # ── Public: Search ────────────────────────────────────────────────────────
# #     def search(self, query: str, top_k: int = 10):
# #         """Simple hybrid search, returns list of product dicts"""
# #         if not self._ready:
# #             # Fallback: simple string search
# #             mask    = self.df["product_name"].str.contains(query, case=False, na=False)
# #             results = self.df[mask].head(top_k)
# #             return self._rows_to_dicts(results)

# #         retrieved = self._hybrid_retrieval(query, top_k=top_k)
# #         return self._rows_to_dicts(retrieved)

# #     # ── Public: Get Products (browsing) ───────────────────────────────────────
# #     def get_products(
# #         self,
# #         page: int = 1,
# #         per_page: int = 20,
# #         category: str = "",
# #         min_price: float = None,
# #         max_price: float = None,
# #         min_rating: float = None,
# #         sort_by: str = "rating",
# #     ):
# #         df = self.df.copy()

# #         # Filter
# #         if category:
# #             df = df[df["top_category"].str.contains(category, case=False, na=False)]
# #         if min_price is not None:
# #             df = df[df["discounted_price"] >= min_price]
# #         if max_price is not None:
# #             df = df[df["discounted_price"] <= max_price]
# #         if min_rating is not None:
# #             df = df[df["rating"] >= min_rating]

# #         # Sort
# #         if sort_by == "price_asc":
# #             df = df.sort_values("discounted_price", ascending=True)
# #         elif sort_by == "price_desc":
# #             df = df.sort_values("discounted_price", ascending=False)
# #         elif sort_by == "discount":
# #             df = df.sort_values("discount_percentage", ascending=False)
# #         else:  # default: rating
# #             df = df.sort_values(["rating", "rating_count"], ascending=False)

# #         total      = len(df)
# #         categories = sorted(self.df["top_category"].dropna().unique().tolist())
# #         start      = (page - 1) * per_page
# #         end        = start + per_page
# #         page_df    = df.iloc[start:end]

# #         return self._rows_to_dicts(page_df), total, categories

# #     # ── Helper ────────────────────────────────────────────────────────────────
# #     def _rows_to_dicts(self, df: pd.DataFrame) -> list:
# #         result = []
# #         for _, row in df.iterrows():
# #             result.append({
# #                 "product_id":          str(row.get("product_id", "")),
# #                 "product_name":        str(row.get("product_name", "")),
# #                 "category":            str(row.get("category", "")),
# #                 "top_category":        str(row.get("top_category", "")),
# #                 "discounted_price":    row.get("discounted_price"),
# #                 "actual_price":        row.get("actual_price"),
# #                 "discount_percentage": row.get("discount_percentage"),
# #                 "rating":              row.get("rating"),
# #                 "rating_count":        row.get("rating_count"),
# #                 "about_product":       str(row.get("about_product", ""))[:400],
# #                 "img_link":            str(row.get("img_link", "")),
# #                 "product_link":        str(row.get("product_link", "")),
# #             })
# #         return result
# """
# Product Recommender Engine
# Hybrid BM25 + FAISS Vector Search + Gemini LLM
# Ported from the Jupyter Notebook NLP project
# """

# import os
# import re
# import json
# import math
# import numpy as np
# import pandas as pd

# # ─── Lazy imports (heavy libs) ────────────────────────────────────────────────
# _faiss = None
# _SentenceTransformer = None
# _BM25Okapi = None
# _genai = None


# def _load_libs():
#     global _faiss, _SentenceTransformer, _BM25Okapi, _genai
#     if _faiss is None:
#         import faiss
#         _faiss = faiss
#     if _SentenceTransformer is None:
#         from sentence_transformers import SentenceTransformer
#         _SentenceTransformer = SentenceTransformer
#     if _BM25Okapi is None:
#         from rank_bm25 import BM25Okapi
#         _BM25Okapi = BM25Okapi
#     if _genai is None:
#         from google import genai
#         _genai = genai


# # ─── Price Cleaner ────────────────────────────────────────────────────────────
# def _clean_price(x):
#     if isinstance(x, str):
#         x = re.sub(r"[₹$,]", "", x).strip()
#         try:
#             return float(x)
#         except ValueError:
#             return None
#     return x


# # ─── Text Combiner ────────────────────────────────────────────────────────────
# def _combine_text(row):
#     return (
#         f"Product Name: {row.get('product_name', '')}\n"
#         f"Category: {row.get('category', '')}\n"
#         f"Description: {row.get('about_product', '')}\n"
#         f"Review Title: {row.get('review_title', '')}\n"
#         f"Review Content: {row.get('review_content', '')}"
#     )


# # ─── Main Class ───────────────────────────────────────────────────────────────
# class ProductRecommender:

#     def __init__(self, dataset_path: str, gemini_api_key: str):
#         print("🔄 Loading dataset …")
#         self.df = self._load_dataset(dataset_path)
#         self.gemini_api_key = gemini_api_key
#         self._bm25 = None
#         self._index = None
#         self._embeddings = None
#         self._embedding_model = None
#         self._gemini_client = None
#         self._ready = False

#         try:
#             _load_libs()
#             self._build_index()
#             self._init_gemini()
#             self._ready = True
#             print("✅ Recommender ready.")
#         except Exception as e:
#             print(f"⚠️  Recommender init error (running in limited mode): {e}")

#     # ── Data Loading ──────────────────────────────────────────────────────────
#     def _load_dataset(self, path: str) -> pd.DataFrame:
#         df = pd.read_csv(path)
#         df["discounted_price"] = df["discounted_price"].apply(_clean_price)
#         df["actual_price"]     = df["actual_price"].apply(_clean_price)
#         df["rating"]           = pd.to_numeric(df["rating"], errors="coerce")
#         df["rating_count"]     = df["rating_count"].astype(str).str.replace(",", "")
#         df["rating_count"]     = pd.to_numeric(df["rating_count"], errors="coerce")
#         df["discount_percentage"] = df["discount_percentage"].astype(str).str.replace("%", "")
#         df["discount_percentage"] = pd.to_numeric(df["discount_percentage"], errors="coerce")
#         df = df.dropna(subset=["product_name", "about_product"])
#         df = df.reset_index(drop=True)
#         # Clean category to top-level only
#         df["top_category"] = df["category"].astype(str).apply(
#             lambda x: x.split("|")[0].strip()
#         )
#         df["combined_text"] = df.apply(_combine_text, axis=1)
#         return df

#     # ── Index Building ────────────────────────────────────────────────────────
#     def _build_index(self):
#         corpus = self.df["combined_text"].tolist()

#         # ── BM25 (always fast, no need to cache) ──────────────────────────────
#         print("🔄 Building BM25 index …")
#         tokenized = [doc.lower().split() for doc in corpus]
#         self._bm25 = _BM25Okapi(tokenized)

#         # ── Cache file paths ───────────────────────────────────────────────────
#         EMBEDDINGS_CACHE = "cache_embeddings.npy"   # NumPy array  (~5 MB)
#         FAISS_CACHE      = "cache_faiss.index"       # FAISS binary (~5 MB)

#         # ── Load from cache if both files exist ────────────────────────────────
#         if os.path.exists(EMBEDDINGS_CACHE) and os.path.exists(FAISS_CACHE):
#             print("⚡ Loading cached embeddings & FAISS index …")
#             self._embeddings = np.load(EMBEDDINGS_CACHE)

#             # Still need the model loaded for encoding new queries at search time
#             self._embedding_model = _SentenceTransformer("all-MiniLM-L6-v2")

#             self._index = _faiss.read_index(FAISS_CACHE)
#             print(f"✅ Loaded from cache — FAISS index: {self._index.ntotal} vectors")

#         # ── Build from scratch and save cache ─────────────────────────────────
#         else:
#             print("🔄 Encoding embeddings (first run — this takes ~5–10 min on CPU) …")
#             self._embedding_model = _SentenceTransformer("all-MiniLM-L6-v2")
#             self._embeddings = self._embedding_model.encode(
#                 corpus, show_progress_bar=True, batch_size=64
#             )

#             # Save embeddings as NumPy file
#             np.save(EMBEDDINGS_CACHE, self._embeddings)
#             print(f"💾 Embeddings saved → {EMBEDDINGS_CACHE}")

#             # Build FAISS index
#             dim = self._embeddings.shape[1]
#             self._index = _faiss.IndexFlatL2(dim)
#             self._index.add(np.array(self._embeddings).astype("float32"))

#             # Save FAISS index to disk
#             _faiss.write_index(self._index, FAISS_CACHE)
#             print(f"💾 FAISS index saved → {FAISS_CACHE}")

#             print(f"✅ FAISS index built: {self._index.ntotal} vectors")

#     def _init_gemini(self):
#         if self.gemini_api_key and self.gemini_api_key != "YOUR_GEMINI_API_KEY_HERE":
#             self._gemini_client = _genai.Client(api_key=self.gemini_api_key)
#             print("✅ Gemini client initialized.")

#     # ── Hybrid Retrieval ──────────────────────────────────────────────────────
#     def _hybrid_retrieval(self, query: str, top_k: int = 5) -> pd.DataFrame:
#         # BM25 scores
#         tokenized_query = query.lower().split()
#         bm25_scores = self._bm25.get_scores(tokenized_query)

#         # Vector search
#         q_emb = self._embedding_model.encode([query])
#         D, I  = self._index.search(np.array(q_emb).astype("float32"), top_k)

#         # Normalize BM25
#         bm25_norm = (bm25_scores - bm25_scores.min()) / (bm25_scores.max() + 1e-9)

#         # Combine scores
#         scores = {}
#         for idx in I[0]:
#             scores[idx] = 0.6 + 0.4 * bm25_norm[idx]

#         for i, idx in enumerate(I[0]):
#             faiss_score = 1 / (1 + D[0][i])  # distance → similarity
#             scores[idx] = scores.get(idx, 0) * faiss_score

#         top_indices = sorted(scores, key=scores.get, reverse=True)[:top_k]
#         return self.df.iloc[top_indices].copy()

#     # ── Build Context for LLM ─────────────────────────────────────────────────
#     def _build_context(self, products_df: pd.DataFrame) -> str:
#         ctx = ""
#         for _, row in products_df.iterrows():
#             ctx += (
#                 f"\nProduct Name: {row['product_name']}\n"
#                 f"Price: ₹{row.get('discounted_price', 'N/A')}\n"
#                 f"Rating: {row.get('rating', 'N/A')}/5\n"
#                 f"Category: {row.get('category', 'N/A')}\n"
#                 f"Description: {row.get('about_product', '')[:300]}\n"
#                 f"Top Review: {str(row.get('review_content', ''))[:200]}\n\n"
#             )
#         return ctx

#     # ── Gemini LLM Call ───────────────────────────────────────────────────────
#     def _call_gemini(self, prompt: str) -> str:
#         if not self._gemini_client:
#             return "⚠️ AI recommendation unavailable. Please configure a valid Gemini API key."
#         response = self._gemini_client.models.generate_content(
#             model="gemini-2.5-flash",
#             contents=prompt,
#         )
#         return response.text

#     # ── Public: Recommend ─────────────────────────────────────────────────────
#     def recommend(self, query: str, top_k: int = 5):
#         """Returns (ai_response_text, list_of_product_dicts)"""
#         if not self._ready:
#             return "Recommender is not initialized.", []

#         retrieved = self._hybrid_retrieval(query, top_k=top_k)
#         context   = self._build_context(retrieved)

#         prompt = (
#             "You are an intelligent e-commerce recommendation assistant.\n\n"
#             f"User Query:\n{query}\n\n"
#             "Based on the following products, recommend the best products.\n"
#             "Show pros and cons of the products in brief.\n"
#             "Explain why each product is suitable based on reviews and ratings.\n"
#             "Format your response with clear sections for each product.\n\n"
#             f"Products:\n{context}"
#         )

#         ai_response = self._call_gemini(prompt)
#         products    = self._rows_to_dicts(retrieved)
#         return ai_response, products

#     # ── Public: Search ────────────────────────────────────────────────────────
#     def search(self, query: str, top_k: int = 10):
#         """Simple hybrid search, returns list of product dicts"""
#         if not self._ready:
#             # Fallback: simple string search
#             mask    = self.df["product_name"].str.contains(query, case=False, na=False)
#             results = self.df[mask].head(top_k)
#             return self._rows_to_dicts(results)

#         retrieved = self._hybrid_retrieval(query, top_k=top_k)
#         return self._rows_to_dicts(retrieved)

#     # ── Public: Get Products (browsing) ───────────────────────────────────────
#     def get_products(
#         self,
#         page: int = 1,
#         per_page: int = 20,
#         category: str = "",
#         min_price: float = None,
#         max_price: float = None,
#         min_rating: float = None,
#         sort_by: str = "rating",
#     ):
#         df = self.df.copy()

#         # Filter
#         if category:
#             df = df[df["top_category"].str.contains(category, case=False, na=False)]
#         if min_price is not None:
#             df = df[df["discounted_price"] >= min_price]
#         if max_price is not None:
#             df = df[df["discounted_price"] <= max_price]
#         if min_rating is not None:
#             df = df[df["rating"] >= min_rating]

#         # Sort
#         if sort_by == "price_asc":
#             df = df.sort_values("discounted_price", ascending=True)
#         elif sort_by == "price_desc":
#             df = df.sort_values("discounted_price", ascending=False)
#         elif sort_by == "discount":
#             df = df.sort_values("discount_percentage", ascending=False)
#         else:  # default: rating
#             df = df.sort_values(["rating", "rating_count"], ascending=False)

#         total      = len(df)
#         categories = sorted(self.df["top_category"].dropna().unique().tolist())
#         start      = (page - 1) * per_page
#         end        = start + per_page
#         page_df    = df.iloc[start:end]

#         return self._rows_to_dicts(page_df), total, categories

#     # ── Helper ────────────────────────────────────────────────────────────────
#     def _rows_to_dicts(self, df: pd.DataFrame) -> list:
#         result = []
#         for _, row in df.iterrows():
#             result.append({
#                 "product_id":          str(row.get("product_id", "")),
#                 "product_name":        str(row.get("product_name", "")),
#                 "category":            str(row.get("category", "")),
#                 "top_category":        str(row.get("top_category", "")),
#                 "discounted_price":    row.get("discounted_price"),
#                 "actual_price":        row.get("actual_price"),
#                 "discount_percentage": row.get("discount_percentage"),
#                 "rating":              row.get("rating"),
#                 "rating_count":        row.get("rating_count"),
#                 "about_product":       str(row.get("about_product", ""))[:400],
#                 "img_link":            str(row.get("img_link", "")),
#                 "product_link":        str(row.get("product_link", "")),
#             })
#         return result
"""
Product Recommender Engine
Hybrid BM25 + FAISS Vector Search + Gemini LLM
Ported from the Jupyter Notebook NLP project
"""

import os
import re
import json
import math
import numpy as np
import pandas as pd

# ─── Lazy imports (heavy libs) ────────────────────────────────────────────────
_faiss = None
_SentenceTransformer = None
_BM25Okapi = None
_genai = None


def _load_libs():
    global _faiss, _SentenceTransformer, _BM25Okapi, _genai
    if _faiss is None:
        import faiss
        _faiss = faiss
    if _SentenceTransformer is None:
        from sentence_transformers import SentenceTransformer
        _SentenceTransformer = SentenceTransformer
    if _BM25Okapi is None:
        from rank_bm25 import BM25Okapi
        _BM25Okapi = BM25Okapi
    if _genai is None:
        from google import genai
        _genai = genai


# ─── Price Cleaner ────────────────────────────────────────────────────────────
def _clean_price(x):
    if isinstance(x, str):
        x = re.sub(r"[₹$,]", "", x).strip()
        try:
            return float(x)
        except ValueError:
            return None
    return x


# ─── Text Combiner ────────────────────────────────────────────────────────────
def _combine_text(row):
    return (
        f"Product Name: {row.get('product_name', '')}\n"
        f"Category: {row.get('category', '')}\n"
        f"Description: {row.get('about_product', '')}\n"
        f"Review Title: {row.get('review_title', '')}\n"
        f"Review Content: {row.get('review_content', '')}"
    )


# ─── Main Class ───────────────────────────────────────────────────────────────
class ProductRecommender:

    def __init__(self, dataset_path: str, gemini_api_key: str):
        print("🔄 Loading dataset …")
        self.df = self._load_dataset(dataset_path)
        self.gemini_api_key = gemini_api_key
        self._bm25 = None
        self._index = None
        self._embeddings = None
        self._embedding_model = None
        self._gemini_client = None
        self._ready = False

        try:
            _load_libs()
            self._build_index()
            self._init_gemini()
            self._ready = True
            print("✅ Recommender ready.")
        except Exception as e:
            print(f"⚠️  Recommender init error (running in limited mode): {e}")

    # ── Data Loading ──────────────────────────────────────────────────────────
    def _load_dataset(self, path: str) -> pd.DataFrame:
        df = pd.read_csv(path)
        df["discounted_price"] = df["discounted_price"].apply(_clean_price)
        df["actual_price"]     = df["actual_price"].apply(_clean_price)
        df["rating"]           = pd.to_numeric(df["rating"], errors="coerce")
        df["rating_count"]     = df["rating_count"].astype(str).str.replace(",", "")
        df["rating_count"]     = pd.to_numeric(df["rating_count"], errors="coerce")
        df["discount_percentage"] = df["discount_percentage"].astype(str).str.replace("%", "")
        df["discount_percentage"] = pd.to_numeric(df["discount_percentage"], errors="coerce")
        df = df.dropna(subset=["product_name", "about_product"])
        df = df.reset_index(drop=True)
        # Clean category to top-level only
        df["top_category"] = df["category"].astype(str).apply(
            lambda x: x.split("|")[0].strip()
        )
        df["combined_text"] = df.apply(_combine_text, axis=1)
        return df

    # ── Index Building ────────────────────────────────────────────────────────
    def _build_index(self):
        corpus = self.df["combined_text"].tolist()

        # ── BM25 (always fast, no need to cache) ──────────────────────────────
        print("🔄 Building BM25 index …")
        tokenized = [doc.lower().split() for doc in corpus]
        self._bm25 = _BM25Okapi(tokenized)

        # ── Cache file paths ───────────────────────────────────────────────────
        EMBEDDINGS_CACHE = "cache_embeddings.npy"   # NumPy array  (~5 MB)
        FAISS_CACHE      = "cache_faiss.index"       # FAISS binary (~5 MB)

        # ── Load from cache if both files exist ────────────────────────────────
        if os.path.exists(EMBEDDINGS_CACHE) and os.path.exists(FAISS_CACHE):
            print("⚡ Loading cached embeddings & FAISS index …")
            self._embeddings = np.load(EMBEDDINGS_CACHE)

            # Still need the model loaded for encoding new queries at search time
            self._embedding_model = _SentenceTransformer("all-MiniLM-L6-v2")

            self._index = _faiss.read_index(FAISS_CACHE)
            print(f"✅ Loaded from cache — FAISS index: {self._index.ntotal} vectors")

        # ── Build from scratch and save cache ─────────────────────────────────
        else:
            print("🔄 Encoding embeddings (first run — this takes ~5~10 min on CPU) …")
            self._embedding_model = _SentenceTransformer("all-MiniLM-L6-v2")
            self._embeddings = self._embedding_model.encode(
                corpus, show_progress_bar=True, batch_size=64
            )

            # Save embeddings as NumPy file
            np.save(EMBEDDINGS_CACHE, self._embeddings)
            print(f"💾 Embeddings saved → {EMBEDDINGS_CACHE}")

            # Build FAISS index
            dim = self._embeddings.shape[1]
            self._index = _faiss.IndexFlatL2(dim)
            self._index.add(np.array(self._embeddings).astype("float32"))

            # Save FAISS index to disk
            _faiss.write_index(self._index, FAISS_CACHE)
            print(f"💾 FAISS index saved → {FAISS_CACHE}")

            print(f"✅ FAISS index built: {self._index.ntotal} vectors")

    def _init_gemini(self):
        if self.gemini_api_key and self.gemini_api_key != "YOUR_GEMINI_API_KEY_HERE":
            self._gemini_client = _genai.Client(api_key=self.gemini_api_key)
            print("✅ Gemini client initialized.")

    # ── Hybrid Retrieval ──────────────────────────────────────────────────────
    def _hybrid_retrieval(self, query: str, top_k: int = 5) -> pd.DataFrame:
        # BM25 scores
        tokenized_query = query.lower().split()
        bm25_scores = self._bm25.get_scores(tokenized_query)

        # Vector search
        q_emb = self._embedding_model.encode([query])
        D, I  = self._index.search(np.array(q_emb).astype("float32"), top_k)

        # Normalize BM25
        bm25_norm = (bm25_scores - bm25_scores.min()) / (bm25_scores.max() + 1e-9)

        # Combine scores
        scores = {}
        for idx in I[0]:
            scores[idx] = 0.6 + 0.4 * bm25_norm[idx]

        for i, idx in enumerate(I[0]):
            faiss_score = 1 / (1 + D[0][i])  # distance → similarity
            scores[idx] = scores.get(idx, 0) * faiss_score

        top_indices = sorted(scores, key=scores.get, reverse=True)[:top_k]
        return self.df.iloc[top_indices].copy()

    # ── Build Context for LLM ─────────────────────────────────────────────────
    def _build_context(self, products_df: pd.DataFrame) -> str:
        ctx = ""
        for _, row in products_df.iterrows():
            ctx += (
                f"\nProduct Name: {row['product_name']}\n"
                f"Price: ₹{row.get('discounted_price', 'N/A')}\n"
                f"Rating: {row.get('rating', 'N/A')}/5\n"
                f"Category: {row.get('category', 'N/A')}\n"
                f"Description: {row.get('about_product', '')[:300]}\n"
                f"Top Review: {str(row.get('review_content', ''))[:200]}\n\n"
            )
        return ctx

    # ── Gemini LLM Call ───────────────────────────────────────────────────────
    def _call_gemini(self, prompt: str) -> str:
        if not self._gemini_client:
            return "⚠️ AI recommendation unavailable. Please configure a valid Gemini API key."
        response = self._gemini_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        return response.text

    # ── Gemini Streaming Call ─────────────────────────────────────────────────
    def _stream_gemini(self, prompt: str):
        """Yields text chunks from Gemini streaming API."""
        if not self._gemini_client:
            yield "⚠️ AI recommendation unavailable. Please configure a valid Gemini API key."
            return
        for chunk in self._gemini_client.models.generate_content_stream(
            model="gemini-2.5-flash",
            contents=prompt,
        ):
            if chunk.text:
                yield chunk.text

    # ── Public: Recommend ─────────────────────────────────────────────────────
    def recommend(self, query: str, top_k: int = 5):
        """Returns (ai_response_text, list_of_product_dicts)"""
        if not self._ready:
            return "Recommender is not initialized.", []

        retrieved = self._hybrid_retrieval(query, top_k=top_k)
        context   = self._build_context(retrieved)

        prompt = (
            "You are an intelligent e-commerce recommendation assistant.\n\n"
            f"User Query:\n{query}\n\n"
            "Based on the following products, recommend the best products.\n"
            "Show pros and cons of the products in brief.\n"
            "Explain why each product is suitable based on reviews and ratings.\n"
            "Format your response with clear sections for each product.\n\n"
            f"Products:\n{context}"
        )

        ai_response = self._call_gemini(prompt)
        products    = self._rows_to_dicts(retrieved)
        return ai_response, products

    # ── Public: Get Retrieved Products (for streaming flow) ──────────────────
    def get_retrieved(self, query: str, top_k: int = 5) -> list:
        """Runs hybrid retrieval and returns product dicts immediately."""
        if not self._ready:
            return []
        retrieved = self._hybrid_retrieval(query, top_k=top_k)
        return self._rows_to_dicts(retrieved)

    # ── Public: Stream Recommend ──────────────────────────────────────────────
    def stream_recommend(self, query: str, products: list):
        """
        Given a query and already-retrieved product dicts,
        streams the Gemini LLM response chunk by chunk.
        """
        if not self._ready:
            yield "Recommender is not initialized."
            return

        # Rebuild context from product dicts
        context = ""
        for p in products:
            context += (
                f"\nProduct Name: {p.get('product_name', '')}\n"
                f"Price: ₹{p.get('discounted_price', 'N/A')}\n"
                f"Rating: {p.get('rating', 'N/A')}/5\n"
                f"Category: {p.get('category', 'N/A')}\n"
                f"Description: {p.get('about_product', '')[:300]}\n\n"
            )

        prompt = (
            "You are an intelligent e-commerce recommendation assistant.\n\n"
            f"User Query:\n{query}\n\n"
            "Based on the following products, recommend the best products.\n"
            "Show pros and cons in brief. Explain why each is suitable using ratings and reviews.\n"
            "Format with clear sections per product.\n\n"
            f"Products:\n{context}"
        )

        yield from self._stream_gemini(prompt)

        prompt = (
            "You are an intelligent e-commerce recommendation assistant.\n\n"
            f"User Query:\n{query}\n\n"
            "Based on the following products, recommend the best products.\n"
            "Show pros and cons of the products in brief.\n"
            "Explain why each product is suitable based on reviews and ratings.\n"
            "Format your response with clear sections for each product.\n\n"
            f"Products:\n{context}"
        )

        ai_response = self._call_gemini(prompt)
        products    = self._rows_to_dicts(retrieved)
        return ai_response, products

    # ── Public: Search ────────────────────────────────────────────────────────
    def search(self, query: str, top_k: int = 10):
        """Simple hybrid search, returns list of product dicts"""
        if not self._ready:
            # Fallback: simple string search
            mask    = self.df["product_name"].str.contains(query, case=False, na=False)
            results = self.df[mask].head(top_k)
            return self._rows_to_dicts(results)

        retrieved = self._hybrid_retrieval(query, top_k=top_k)
        return self._rows_to_dicts(retrieved)

    # ── Public: Get Products (browsing) ───────────────────────────────────────
    def get_products(
        self,
        page: int = 1,
        per_page: int = 20,
        category: str = "",
        min_price: float = None,
        max_price: float = None,
        min_rating: float = None,
        sort_by: str = "rating",
    ):
        df = self.df.copy()

        # Filter
        if category:
            df = df[df["top_category"].str.contains(category, case=False, na=False)]
        if min_price is not None:
            df = df[df["discounted_price"] >= min_price]
        if max_price is not None:
            df = df[df["discounted_price"] <= max_price]
        if min_rating is not None:
            df = df[df["rating"] >= min_rating]

        # Sort
        if sort_by == "price_asc":
            df = df.sort_values("discounted_price", ascending=True)
        elif sort_by == "price_desc":
            df = df.sort_values("discounted_price", ascending=False)
        elif sort_by == "discount":
            df = df.sort_values("discount_percentage", ascending=False)
        else:  # default: rating
            df = df.sort_values(["rating", "rating_count"], ascending=False)

        total      = len(df)
        categories = sorted(self.df["top_category"].dropna().unique().tolist())
        start      = (page - 1) * per_page
        end        = start + per_page
        page_df    = df.iloc[start:end]

        return self._rows_to_dicts(page_df), total, categories

    # ── Helper ────────────────────────────────────────────────────────────────
    def _rows_to_dicts(self, df: pd.DataFrame) -> list:
        result = []
        for _, row in df.iterrows():
            result.append({
                "product_id":          str(row.get("product_id", "")),
                "product_name":        str(row.get("product_name", "")),
                "category":            str(row.get("category", "")),
                "top_category":        str(row.get("top_category", "")),
                "discounted_price":    row.get("discounted_price"),
                "actual_price":        row.get("actual_price"),
                "discount_percentage": row.get("discount_percentage"),
                "rating":              row.get("rating"),
                "rating_count":        row.get("rating_count"),
                "about_product":       str(row.get("about_product", ""))[:400],
                "img_link":            str(row.get("img_link", "")),
                "product_link":        str(row.get("product_link", "")),
            })
        return result