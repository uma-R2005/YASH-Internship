import json
import math
import urllib.request
import urllib.error
from http.server import HTTPServer, BaseHTTPRequestHandler

COHERE_API_KEY = "Kr657M4P3N1QQkmfWCwLzBK9iY2weny7ZPcFCO4t"
COHERE_URL     = "https://api.cohere.com/v2/embed"
COHERE_MODEL   = "embed-english-light-v3.0"
K              = 60

PRODUCTS = [
  {"id":1,"emoji":"👟","category":"Footwear","title":"Nike Air Max 270","description":"Lightweight running shoe with cushioned foam sole and breathable mesh upper. Designed for daily training.","price":129},
  {"id":2,"emoji":"👟","category":"Footwear","title":"Adidas Ultraboost 22","description":"Premium running shoe with Boost midsole for energy return. Fits comfortably for long distance jogging.","price":180},
  {"id":3,"emoji":"👟","category":"Footwear","title":"Puma Softride Enzo","description":"Casual walking shoe with soft cushioned sole for everyday comfort. Ideal for long walks and light activity.","price":65},
  {"id":4,"emoji":"🎧","category":"Audio","title":"Sony WH-1000XM5","description":"Industry-leading wireless noise-cancelling headphones with 30-hour battery. Crystal clear audio for music lovers.","price":349},
  {"id":5,"emoji":"🎧","category":"Audio","title":"JBL Tune 510BT","description":"Budget wireless on-ear headphones with 40-hour playtime and pure bass sound. Great value for everyday listening.","price":49},
  {"id":6,"emoji":"💻","category":"Laptops","title":"MacBook Air M2","description":"Thin and lightweight laptop with Apple M2 chip. Silent fanless design, 18-hour battery, brilliant Retina display.","price":1099},
  {"id":7,"emoji":"💻","category":"Laptops","title":"Acer Aspire 5","description":"Affordable budget laptop for students. AMD Ryzen processor, 8GB RAM, 512GB SSD, full HD display.","price":449},
  {"id":8,"emoji":"🎒","category":"Bags","title":"Osprey Daylite Backpack","description":"Lightweight daypack for hiking and outdoor adventures. Waterproof material, 13L capacity, ergonomic straps.","price":55},
  {"id":9,"emoji":"🎒","category":"Bags","title":"Samsonite Laptop Bag","description":"Professional business laptop bag with multiple compartments. Water resistant, padded sleeve, fits 15-inch laptops.","price":89},
  {"id":10,"emoji":"🧴","category":"Beauty","title":"CeraVe Moisturizing Cream","description":"Dermatologist recommended daily moisturizer for dry and sensitive skin. Fragrance-free, non-comedogenic.","price":19},
  {"id":11,"emoji":"🧴","category":"Beauty","title":"Neutrogena Sunscreen SPF 50","description":"Lightweight sunscreen lotion with SPF 50 protection. Non-greasy formula, water resistant, dermatologist approved.","price":14},
  {"id":12,"emoji":"⌚","category":"Wearables","title":"Apple Watch Series 9","description":"Smartwatch with health tracking, GPS, always-on Retina display. ECG, blood oxygen sensor, fitness monitoring.","price":399},
]

STOP_WORDS = {'a','an','the','for','with','and','or','to','of','in','on','at','by','as','is','are','was','were','be','been','has','have','had','do','does','did','not','but','if','its','it','this','that','these','those','from','up','out','into'}

def tokenize(text):
    tokens = text.lower().replace('-',' ')
    tokens = ''.join(c if c.isalnum() or c==' ' else ' ' for c in tokens)
    return [t for t in tokens.split() if len(t)>1 and t not in STOP_WORDS]

def build_idf():
    print("[TF-IDF] Building IDF index across all products...")
    N  = len(PRODUCTS)
    df = {}
    for p in PRODUCTS:
        tokens = set(tokenize(p['title'] + ' ' + p['description']))
        for t in tokens:
            df[t] = df.get(t, 0) + 1
    idf = {t: math.log((N+1)/(df[t]+1))+1 for t in df}
    print("[TF-IDF] IDF index built - " + str(len(idf)) + " unique tokens indexed")
    return idf

IDF = build_idf()

def tfidf_score(query, product):
    q_tokens   = tokenize(query)
    if not q_tokens:
        return 0.0, []
    doc_tokens = tokenize(product['title'] + ' ' + product['description'])
    doc_len    = len(doc_tokens)
    tf = {}
    for t in doc_tokens:
        tf[t] = tf.get(t, 0) + 1
    for t in tf:
        tf[t] /= doc_len
    score   = 0.0
    matched = []
    for qt in q_tokens:
        if qt in tf:
            score += tf[qt] * IDF.get(qt, 1.0)
            matched.append(qt)
    return score / max(len(q_tokens), 1), matched

def cohere_embed(texts, input_type):
    payload = json.dumps({
        "model":           COHERE_MODEL,
        "texts":           texts,
        "input_type":      input_type,
        "embedding_types": ["float"]
    }).encode("utf-8")
    req = urllib.request.Request(
        COHERE_URL,
        data    = payload,
        headers = {
            "Authorization": "Bearer " + COHERE_API_KEY,
            "Content-Type":  "application/json"
        },
        method = "POST"
    )
    with urllib.request.urlopen(req) as res:
        data = json.loads(res.read())
    return data["embeddings"]["float"]

def cosine_sim(a, b):
    dot  = sum(x*y for x,y in zip(a,b))
    magA = math.sqrt(sum(x*x for x in a))
    magB = math.sqrt(sum(x*x for x in b))
    return dot/(magA*magB) if magA*magB else 0.0

print("[COHERE] Embedding all " + str(len(PRODUCTS)) + " products in one batch call...")
texts           = [p['title'] + ". " + p['description'] for p in PRODUCTS]
PRODUCT_VECTORS = cohere_embed(texts, "search_document")
print("[COHERE] " + str(len(PRODUCT_VECTORS)) + " product vectors stored - each is " + str(len(PRODUCT_VECTORS[0])) + " dimensions")

def search(query, mode):
    print("\n" + "="*60)
    print("[SEARCH] Query: '" + query + "' | Mode: " + mode.upper())
    print("="*60)

    print("\n[STEP 1] Running TF-IDF on all products...")
    kw_results = [tfidf_score(query, p) for p in PRODUCTS]
    for i, (score, matched) in enumerate(kw_results):
        if score > 0:
            print("  MATCH  " + PRODUCTS[i]['title'] + ": TF-IDF=" + str(round(score,4)) + " matched=" + str(matched))
        else:
            print("  MISS   " + PRODUCTS[i]['title'] + ": TF-IDF=0 (no exact match)")

    print("\n[STEP 2] Embedding query via Cohere API...")
    q_vec = cohere_embed([query], "search_query")[0]
    print("[STEP 2] Query vector received - " + str(len(q_vec)) + " dimensions")

    print("\n[STEP 3] Computing cosine similarity for all products...")
    sem_scores = [cosine_sim(q_vec, pv) for pv in PRODUCT_VECTORS]
    for i, score in enumerate(sem_scores):
        print("  " + PRODUCTS[i]['title'] + ": Cosine=" + str(round(score,4)))

    scored = []
    for i, p in enumerate(PRODUCTS):
        scored.append({
            "product":   p,
            "kw_score":  kw_results[i][0],
            "sem_score": sem_scores[i],
            "matched":   kw_results[i][1],
            "hyb_score": 0.0,
            "kw_rank":   0,
            "sem_rank":  0,
        })

    print("\n[STEP 4] Assigning KW and Semantic ranks...")
    for rank, s in enumerate(sorted(scored, key=lambda x: x['kw_score'],  reverse=True), 1):
        s['kw_rank']  = rank
    for rank, s in enumerate(sorted(scored, key=lambda x: x['sem_score'], reverse=True), 1):
        s['sem_rank'] = rank

    print("\n[STEP 5] Computing RRF scores (k=" + str(K) + ")...")
    for s in scored:
        s['hyb_score'] = 1/(K+s['kw_rank']) + 1/(K+s['sem_rank'])
        print("  " + s['product']['title'] + ": KW_rank=#" + str(s['kw_rank']) + " Sem_rank=#" + str(s['sem_rank']) + " RRF=" + str(round(s['hyb_score'],5)))

    if   mode == 'keyword':  scored.sort(key=lambda x: x['kw_score'],  reverse=True)
    elif mode == 'semantic': scored.sort(key=lambda x: x['sem_score'], reverse=True)
    else:                    scored.sort(key=lambda x: x['hyb_score'], reverse=True)

    filtered = [s for s in scored if s['kw_score']>0.001 or s['sem_score']>0.01]
    max_hyb  = max((s['hyb_score'] for s in filtered), default=0.001)

    print("\n[RESULT] Final ranking by " + mode.upper() + ":")
    results = []
    for i, s in enumerate(filtered):
        print("  #" + str(i+1) + " " + s['product']['title'] + " - TF-IDF:" + str(round(s['kw_score'],4)) + " Cosine:" + str(round(s['sem_score'],4)) + " RRF:" + str(round(s['hyb_score'],5)))
        results.append({
            "id":        s['product']['id'],
            "emoji":     s['product']['emoji'],
            "category":  s['product']['category'],
            "title":     s['product']['title'],
            "desc":      s['product']['description'],
            "price":     s['product']['price'],
            "kw_score":  round(s['kw_score'],  4),
            "sem_score": round(s['sem_score'], 4),
            "hyb_score": round(s['hyb_score'], 5),
            "hyb_norm":  round(s['hyb_score']/max_hyb, 4),
            "kw_rank":   s['kw_rank'],
            "sem_rank":  s['sem_rank'],
            "matched":   s['matched'],
        })

    print("\n[SEARCH] Done - " + str(len(results)) + " results returned to browser")
    return results


def explain_ranking(product, rank, query, mode, all_results):
    print("\n[EXPLAIN] Generating explanation for '" + product['title'] + "' rank #" + str(rank))

    title     = product['title']
    kw_score  = product['kw_score']
    sem_score = product['sem_score']
    hyb_score = product['hyb_score']
    kw_rank   = product['kw_rank']
    sem_rank  = product['sem_rank']
    matched   = product['matched']
    total     = len(all_results)

    lines = []

    lines.append("RANKING SUMMARY")
    lines.append("-" * 40)
    if rank == 1:
        lines.append(title + " ranked #1 — the strongest match for your query \"" + query + "\".")
    else:
        lines.append(title + " ranked #" + str(rank) + " out of " + str(total) + " results for \"" + query + "\".")
    lines.append("")

    lines.append("1. KEYWORD SCORE (TF-IDF) = " + str(kw_score))
    lines.append("-" * 40)
    if kw_score > 0 and matched:
        lines.append("Exact keyword matches found: " + str(matched))
        lines.append("")
        lines.append("How TF-IDF works here:")
        lines.append("  TF  = occurrences of matched word / total words in product text")
        lines.append("  IDF = log((total products + 1) / (products with this word + 1)) + 1")
        lines.append("  Score = sum of (TF x IDF) / number of query words")
        lines.append("")
        lines.append("The matched word(s) " + str(matched) + " appear in the product description.")
        lines.append("Rare words score higher because fewer products contain them — higher IDF value.")
        lines.append("Keyword rank: #" + str(kw_rank) + " out of 12 products.")
    else:
        lines.append("No exact keyword matches found for query words in this product's title or description.")
        lines.append("TF-IDF score = 0 because none of the query tokens appear verbatim in this product.")
        lines.append("")
        lines.append("This is the key limitation of keyword search — it only scores exact word matches.")
        lines.append("This product appeared because its semantic score kept it relevant despite zero keyword score.")
    lines.append("")

    lines.append("2. SEMANTIC SCORE (Cosine Similarity) = " + str(sem_score))
    lines.append("-" * 40)
    if sem_score >= 0.5:
        sem_label = "Very High"
        sem_meaning = "The meaning of your query closely aligns with this product. Cohere placed both vectors in nearly the same direction in high-dimensional space."
    elif sem_score >= 0.35:
        sem_label = "High"
        sem_meaning = "Good semantic overlap. The neural network understands that your query and this product share similar meaning even without exact word matches."
    elif sem_score >= 0.2:
        sem_label = "Moderate"
        sem_meaning = "Some semantic similarity. The product partially relates to your query's meaning but they are not closely related concepts."
    else:
        sem_label = "Low"
        sem_meaning = "Weak semantic match. This product's meaning is quite different from your query in the embedding space."

    lines.append("Semantic similarity level: " + sem_label)
    lines.append("")
    lines.append("How cosine similarity works:")
    lines.append("  Step 1: Cohere API embedded your query into a 384-dimensional vector")
    lines.append("  Step 2: At startup, all 12 product descriptions were embedded into 384-dimensional vectors")
    lines.append("  Step 3: Cosine similarity = dot_product(query, product) / (magnitude_query x magnitude_product)")
    lines.append("  Step 4: Score of 1.0 = identical meaning | 0.0 = completely unrelated")
    lines.append("")
    lines.append(sem_meaning)
    lines.append("Semantic rank: #" + str(sem_rank) + " out of 12 products.")
    lines.append("")

    lines.append("3. HYBRID SCORE (Reciprocal Rank Fusion) = " + str(hyb_score))
    lines.append("-" * 40)
    lines.append("RRF formula: 1/(60 + kw_rank) + 1/(60 + sem_rank)")
    lines.append("")
    lines.append("Calculation for " + title + ":")
    lines.append("  1/(60 + " + str(kw_rank) + ") + 1/(60 + " + str(sem_rank) + ")")
    lines.append("  = 1/" + str(60+kw_rank) + " + 1/" + str(60+sem_rank))
    lines.append("  = " + str(round(1/(60+kw_rank),5)) + " + " + str(round(1/(60+sem_rank),5)))
    lines.append("  = " + str(hyb_score))
    lines.append("")
    lines.append("k=60 is the industry-standard dampening constant used by Elasticsearch and Pinecone.")
    lines.append("RRF uses rank positions only — never raw scores. This makes it scale-independent.")
    lines.append("A product ranked #1 in both keyword and semantic always wins hybrid search.")
    lines.append("")

    lines.append("4. COMPARISON WITH OTHER PRODUCTS")
    lines.append("-" * 40)
    others = [r for r in all_results if r['title'] != title][:3]
    for other in others:
        o_rank = all_results.index(other) + 1
        kw_compare  = "higher TF-IDF (" + str(other['kw_score']) + " vs " + str(kw_score) + ")" if other['kw_score'] > kw_score else ("lower TF-IDF (" + str(other['kw_score']) + " vs " + str(kw_score) + ")" if other['kw_score'] < kw_score else "same TF-IDF")
        sem_compare = "higher cosine (" + str(other['sem_score']) + " vs " + str(sem_score) + ")" if other['sem_score'] > sem_score else ("lower cosine (" + str(other['sem_score']) + " vs " + str(sem_score) + ")" if other['sem_score'] < sem_score else "same cosine")
        lines.append("  vs " + other['title'] + " (ranked #" + str(o_rank) + "):")
        lines.append("     " + kw_compare + ", " + sem_compare)
    lines.append("")

    lines.append("5. WHAT WOULD IMPROVE THIS PRODUCT'S RANK")
    lines.append("-" * 40)
    if kw_score == 0:
        lines.append("- Add exact query keywords to the product title or description.")
        lines.append("  Currently no words from \"" + query + "\" appear verbatim in this product.")
    else:
        lines.append("- Keyword match is already contributing. Adding more query-relevant terms would help further.")
    if sem_score < 0.5:
        lines.append("- Enrich the product description with semantically related terms.")
        lines.append("  Semantic score of " + str(sem_score) + " shows limited conceptual overlap with the query.")
    else:
        lines.append("- Semantic score of " + str(sem_score) + " is already strong. Maintaining a rich description helps.")
    if kw_rank > 3 and sem_rank > 3:
        lines.append("- Both keyword (#" + str(kw_rank) + ") and semantic (#" + str(sem_rank) + ") ranks are above #3. Improving either one would boost the hybrid score.")

    explanation = "\n".join(lines)
    print("[EXPLAIN] Done - " + str(len(explanation)) + " characters")
    return explanation


class Handler(BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        pass

    def send_cors(self):
        self.send_header("Access-Control-Allow-Origin",  "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_cors()
        self.end_headers()

    def do_POST(self):
        if self.path == "/search":
            try:
                length  = int(self.headers["Content-Length"])
                body    = json.loads(self.rfile.read(length))
                query   = body.get("query", "").strip()
                mode    = body.get("mode",  "keyword")
                if not query:
                    raise ValueError("Empty query")
                results = search(query, mode)
                out     = json.dumps({"results": results}).encode("utf-8")
                self.send_response(200)
                self.send_cors()
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(out)
            except Exception as e:
                print("\n[ERROR] Search failed: " + str(e))
                self.send_response(500)
                self.send_cors()
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())

        elif self.path == "/explain":
            try:
                length      = int(self.headers["Content-Length"])
                body        = json.loads(self.rfile.read(length))
                product     = body.get("product")
                rank        = body.get("rank")
                query       = body.get("query")
                mode        = body.get("mode")
                all_results = body.get("all_results", [])
                explanation = explain_ranking(product, rank, query, mode, all_results)
                out         = json.dumps({"explanation": explanation}).encode("utf-8")
                self.send_response(200)
                self.send_cors()
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(out)
            except Exception as e:
                print("\n[ERROR] Explain failed: " + str(e))
                self.send_response(500)
                self.send_cors()
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())

        else:
            self.send_response(404)
            self.end_headers()

    def do_GET(self):
        import os
        path = "index.html" if self.path in ["/", "/index.html"] else self.path.lstrip("/")
        if os.path.exists(path):
            self.send_response(200)
            self.send_cors()
            if   path.endswith(".js"):   self.send_header("Content-Type", "application/javascript")
            elif path.endswith(".css"):  self.send_header("Content-Type", "text/css")
            elif path.endswith(".html"): self.send_header("Content-Type", "text/html")
            self.end_headers()
            with open(path, "rb") as f:
                self.wfile.write(f.read())
        else:
            self.send_response(404)
            self.end_headers()

if __name__ == "__main__":
    PORT = 8000
    print("="*60)
    print("   SearchLab - E-commerce Search Engine")
    print("="*60)
    print("Server running at: http://localhost:" + str(PORT))
    print("Cohere model:      " + COHERE_MODEL)
    print("Explanation:       Pure Python (instant, no API needed)")
    print("Products loaded:   " + str(len(PRODUCTS)))
    print("="*60)
    print("Press Ctrl+C to stop\n")
    HTTPServer(("", PORT), Handler).serve_forever()