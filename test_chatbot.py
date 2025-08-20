#!/usr/bin/env python3
"""
Test script for AI Chatbot functionality in FOB Test Analysis Dashboard
"""

import google.generativeai as genai

# Gemini AI Configuration
GEMINI_API_KEY = "AIzaSyBkw6dqrouC-Jl8Xe3QiyP83lOQTPdWYmQ"

def configure_gemini():
    """Configure Gemini AI with stored API key"""
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        return True
    except Exception as e:
        print(f"Error configuring Gemini AI: {str(e)}")
        return False

def generate_chatbot_response(user_message, language='en'):
    """Generate chatbot response using Gemini AI"""
    try:
        # Configure Gemini
        if not configure_gemini():
            return "Error: Failed to configure Gemini AI"
        
        # Create chatbot prompt
        if language == 'zh':
            prompt = f"""
你是一个专业的FOB测试分析仪表板助手。请用中文回答用户的问题。

用户问题：{user_message}

请提供以下帮助：
1. 如果询问如何使用仪表板，请提供详细的步骤说明
2. 如果询问FOB测试，请解释相关概念和流程
3. 如果询问数据分析，请提供专业建议
4. 如果询问功能特性，请详细说明
5. 保持友好、专业、有帮助的态度

请用中文回答，格式要清晰易懂。
"""
        else:
            prompt = f"""
You are a professional FOB Test Analysis Dashboard assistant. Please answer the user's question in English.

User Question: {user_message}

Please provide the following help:
1. If asking about how to use the dashboard, provide detailed step-by-step instructions
2. If asking about FOB testing, explain related concepts and procedures
3. If asking about data analysis, provide professional advice
4. If asking about features, explain in detail
5. Maintain a friendly, professional, and helpful attitude

Please answer in English with clear and understandable format.
"""
        
        # Try different models with fallback
        try:
            genai.configure(api_key=GEMINI_API_KEY)
            model = genai.GenerativeModel('gemini-2.0-flash-lite')
        except:
            model = genai.GenerativeModel('gemini-1.5-flash')
        
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error generating chatbot response: {str(e)}"

def test_chatbot():
    """Test chatbot functionality"""
    print("🤖 Testing AI Chatbot for FOB Dashboard")
    print("=" * 50)
    
    # Test questions
    test_questions = [
        "How do I create a new project?",
        "What is FOB testing?",
        "How do I analyze body weight data?",
        "What are the different analysis modes?",
        "How do I generate an AI report?"
    ]
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n{i}. Testing question: {question}")
        print("-" * 40)
        
        response = generate_chatbot_response(question, 'en')
        print(f"AI Response: {response}")
        print("=" * 50)
    
    # Test Chinese
    print("\n🇨🇳 Testing Chinese chatbot...")
    chinese_question = "如何使用这个仪表板？"
    print(f"Question: {chinese_question}")
    chinese_response = generate_chatbot_response(chinese_question, 'zh')
    print(f"AI Response: {chinese_response}")

if __name__ == "__main__":
    test_chatbot()
