import streamlit as st
import pdfplumber
import os
from dotenv import load_dotenv
from openai import OpenAI
from tavily import TavilyClient
import json
from typing import List, Dict, Any

# Load environment variables
load_dotenv()

# Initialize API clients
@st.cache_resource
def init_clients():
    """Initialize OpenAI and Tavily clients"""
    openai_key = os.getenv("OPENAI_API_KEY")
    tavily_key = os.getenv("TAVILY_API_KEY")
    
    if not openai_key:
        st.error("OPENAI_API_KEY not found in environment variables")
        return None, None
    
    if not tavily_key:
        st.error("TAVILY_API_KEY not found in environment variables")
        return None, None
    
    openai_client = OpenAI(api_key=openai_key)
    tavily_client = TavilyClient(api_key=tavily_key)
    
    return openai_client, tavily_client

def extract_text_from_pdf(pdf_file) -> str:
    """Extract text content from uploaded PDF"""
    try:
        text = ""
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text
    except Exception as e:
        st.error(f"Error extracting text from PDF: {str(e)}")
        return ""

def extract_claims(text: str, openai_client: OpenAI) -> List[Dict[str, Any]]:
    """Extract verifiable claims from the text using OpenAI"""
    try:
        # Limit text length to avoid token limits (8000 chars is roughly 2000 tokens)
        max_text_length = 8000
        if len(text) > max_text_length:
            text_to_analyze = text[:max_text_length]
            st.info(f"⚠️ Document is large. Analyzing first {max_text_length} characters. Consider splitting large documents.")
        else:
            text_to_analyze = text
        
        prompt = f"""Analyze the following text and extract all verifiable claims. Focus on:
- Statistics and numerical data
- Dates and historical events
- Financial figures (prices, GDP, market values, etc.)
- Technical specifications
- Scientific facts
- Demographic data
- Any factual statements that can be verified

For each claim, extract:
1. The exact claim text
2. The type of claim (statistic, date, financial, technical, scientific, demographic, or other)
3. The key entities involved

Return the results as a JSON object with a "claims" array. Structure:
{{
  "claims": [
    {{
      "claim": "exact claim text from document",
      "type": "statistic|date|financial|technical|scientific|demographic|other",
      "entities": ["entity1", "entity2"]
    }}
  ]
}}

Text to analyze:
{text_to_analyze}

Return ONLY valid JSON, no additional text."""

        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a fact-checking assistant. Extract verifiable claims from text and return them as JSON with a 'claims' array."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        
        # Extract claims array from result
        if isinstance(result, dict) and "claims" in result:
            claims = result["claims"]
        elif isinstance(result, list):
            claims = result
        else:
            claims = []
        
        return claims if isinstance(claims, list) else []
    
    except json.JSONDecodeError as e:
        st.error(f"Error parsing JSON response: {str(e)}")
        return []
    except Exception as e:
        st.error(f"Error extracting claims: {str(e)}")
        return []

def search_web_for_claim(claim: str, claim_type: str, tavily_client: TavilyClient) -> Dict[str, Any]:
    """Search the web for information about a claim"""
    try:
        # Build search query
        search_query = f"{claim}"
        
        # Perform search
        response = tavily_client.search(
            query=search_query,
            search_depth="advanced",
            max_results=5
        )
        
        return {
            "results": response.get("results", []),
            "query": search_query
        }
    except Exception as e:
        st.error(f"Error searching web: {str(e)}")
        return {"results": [], "query": claim}

def verify_claim(claim: Dict[str, Any], search_results: Dict[str, Any], openai_client: OpenAI) -> Dict[str, Any]:
    """Verify a claim against web search results using OpenAI"""
    try:
        claim_text = claim.get("claim", "")
        claim_type = claim.get("type", "other")
        
        # Prepare search results context
        search_context = ""
        if search_results.get("results"):
            for i, result in enumerate(search_results["results"][:3], 1):
                title = result.get('title', 'N/A')
                content = result.get('content', 'N/A')[:500]  # Limit content length
                url = result.get('url', 'N/A')
                search_context += f"\nSource {i}:\nTitle: {title}\nContent: {content}\nURL: {url}\n"
        
        prompt = f"""You are a fact-checker. Verify the following claim against the provided web search results.

Claim to verify:
"{claim_text}"

Claim Type: {claim_type}

Web Search Results:
{search_context if search_context else "No search results found."}

Based on the search results, determine:
1. Is the claim VERIFIED (matches current data), INACCURATE (outdated or partially wrong), or FALSE (no evidence or contradicts evidence)?
2. What is the correct/current information if the claim is inaccurate or false?
3. Provide a brief explanation.

Return your response as JSON with this structure:
{{
  "status": "VERIFIED|INACCURATE|FALSE",
  "explanation": "brief explanation of your verification",
  "correct_info": "correct information if status is INACCURATE or FALSE, otherwise null",
  "confidence": "HIGH|MEDIUM|LOW"
}}

Return ONLY valid JSON, no additional text."""

        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a professional fact-checker. Analyze claims against evidence and provide accurate verification."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            response_format={"type": "json_object"}
        )
        
        verification = json.loads(response.choices[0].message.content)
        
        return {
            "claim": claim_text,
            "type": claim_type,
            "status": verification.get("status", "UNKNOWN"),
            "explanation": verification.get("explanation", ""),
            "correct_info": verification.get("correct_info"),
            "confidence": verification.get("confidence", "MEDIUM"),
            "sources": [r.get("url", "") for r in search_results.get("results", [])[:3] if r.get("url")]
        }
    
    except json.JSONDecodeError as e:
        st.warning(f"Error parsing verification response for claim: {claim.get('claim', '')[:50]}...")
        return {
            "claim": claim.get("claim", ""),
            "type": claim.get("type", "other"),
            "status": "ERROR",
            "explanation": f"Error parsing verification response: {str(e)}",
            "correct_info": None,
            "confidence": "LOW",
            "sources": []
        }
    except Exception as e:
        st.warning(f"Error verifying claim: {claim.get('claim', '')[:50]}... - {str(e)}")
        return {
            "claim": claim.get("claim", ""),
            "type": claim.get("type", "other"),
            "status": "ERROR",
            "explanation": f"Error during verification: {str(e)}",
            "correct_info": None,
            "confidence": "LOW",
            "sources": []
        }

def get_status_color(status: str) -> str:
    """Get color for status badge"""
    status_colors = {
        "VERIFIED": "#28a745",
        "INACCURATE": "#ffc107",
        "FALSE": "#dc3545",
        "ERROR": "#6c757d",
        "UNKNOWN": "#6c757d"
    }
    return status_colors.get(status, "#6c757d")

def get_status_emoji(status: str) -> str:
    """Get emoji for status"""
    status_emojis = {
        "VERIFIED": "✅",
        "INACCURATE": "⚠️",
        "FALSE": "❌",
        "ERROR": "⚠️",
        "UNKNOWN": "❓"
    }
    return status_emojis.get(status, "❓")

def main():
    st.set_page_config(
        page_title="Fact-Checking Web App",
        page_icon="🔍",
        layout="wide"
    )
    
    st.title("🔍 Fact-Checking Web App")
    st.markdown("Upload a PDF document to extract and verify claims against live web data.")
    
    # Initialize clients
    openai_client, tavily_client = init_clients()
    
    if openai_client is None or tavily_client is None:
        st.warning("Please set up your API keys in the .env file. See README for instructions.")
        st.stop()
    
    # File upload
    uploaded_file = st.file_uploader(
        "Upload PDF Document",
        type=["pdf"],
        help="Upload a PDF file containing claims to verify"
    )
    
    if uploaded_file is not None:
        # Process PDF
        with st.spinner("Extracting text from PDF..."):
            pdf_text = extract_text_from_pdf(uploaded_file)
        
        if not pdf_text:
            st.error("Could not extract text from PDF. Please ensure the PDF contains readable text.")
            st.stop()
        
        st.success(f"✅ Extracted {len(pdf_text)} characters from PDF")
        
        # Extract claims
        with st.spinner("Analyzing document and extracting claims..."):
            claims = extract_claims(pdf_text, openai_client)
        
        if not claims:
            st.warning("No verifiable claims found in the document.")
            st.stop()
        
        st.success(f"✅ Found {len(claims)} verifiable claims")
        
        # Show claims preview
        with st.expander("📋 Extracted Claims Preview", expanded=False):
            for i, claim in enumerate(claims, 1):
                st.markdown(f"**{i}. {claim.get('claim', 'N/A')[:100]}...**")
                st.caption(f"Type: {claim.get('type', 'unknown')}")
        
        # Verify claims button
        if st.button("🔍 Verify All Claims", type="primary", use_container_width=True):
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            results = []
            total_claims = len(claims)
            
            for idx, claim in enumerate(claims):
                status_text.text(f"Verifying claim {idx + 1} of {total_claims}...")
                progress_bar.progress((idx) / total_claims)
                
                # Search web
                search_results = search_web_for_claim(
                    claim.get("claim", ""),
                    claim.get("type", "other"),
                    tavily_client
                )
                
                # Verify claim
                verification = verify_claim(claim, search_results, openai_client)
                results.append(verification)
            
            progress_bar.progress(1.0)
            status_text.text("✅ Verification complete!")
            
            # Store results in session state
            st.session_state['verification_results'] = results
            
            # Force rerun to show results
            st.rerun()
        
        # Display results if available
        if 'verification_results' in st.session_state:
            results = st.session_state['verification_results']
            
            st.markdown("---")
            st.header("📊 Verification Results")
            
            # Summary statistics
            status_counts = {}
            for result in results:
                status = result.get("status", "UNKNOWN")
                status_counts[status] = status_counts.get(status, 0) + 1
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Claims", len(results))
            with col2:
                verified = status_counts.get("VERIFIED", 0)
                st.metric("✅ Verified", verified, delta=f"{verified/len(results)*100:.1f}%")
            with col3:
                inaccurate = status_counts.get("INACCURATE", 0)
                st.metric("⚠️ Inaccurate", inaccurate, delta=f"{inaccurate/len(results)*100:.1f}%")
            with col4:
                false_claims = status_counts.get("FALSE", 0)
                st.metric("❌ False", false_claims, delta=f"{false_claims/len(results)*100:.1f}%")
            
            # Detailed results
            st.markdown("### Detailed Results")
            
            for idx, result in enumerate(results, 1):
                status = result.get("status", "UNKNOWN")
                status_emoji = get_status_emoji(status)
                status_color = get_status_color(status)
                
                with st.container():
                    st.markdown(f"#### {status_emoji} Claim {idx}: {status}")
                    
                    # Claim details
                    st.markdown(f"**Claim:** {result.get('claim', 'N/A')}")
                    st.markdown(f"**Type:** {result.get('type', 'unknown').title()}")
                    st.markdown(f"**Confidence:** {result.get('confidence', 'MEDIUM')}")
                    
                    # Explanation
                    st.markdown(f"**Explanation:** {result.get('explanation', 'No explanation provided.')}")
                    
                    # Correct info if available
                    if result.get('correct_info'):
                        st.info(f"**Correct Information:** {result.get('correct_info')}")
                    
                    # Sources
                    sources = result.get('sources', [])
                    if sources:
                        st.markdown("**Sources:**")
                        for source_url in sources:
                            if source_url:
                                st.markdown(f"- [{source_url}]({source_url})")
                    
                    st.markdown("---")

if __name__ == "__main__":
    main()

