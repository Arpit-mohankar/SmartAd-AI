# 🧠 AdSmart AI

**Intelligent advertising, automated** - Transform manual keyword research into AI-powered campaign creation.

[![Made by](https://img.shields.io/badge/Made%20by-Arpit%20Mohankar-blue)](https://github.com/yourhandle)
[![Python](https://img.shields.io/badge/Python-3.8+-green)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red)](https://streamlit.io)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

> AI-powered SEM keyword research tool that generates Google Ads campaigns in minutes, not hours.

## 🚀 Features

- **🤖 AI Website Analysis** - Understands your business automatically
- **🔍 Competitor Research** - Finds keyword opportunities from competitor sites
- **📊 SERP Data Mining** - Gets real search volumes and competition data
- **🎯 Smart Categorization** - Organizes keywords into professional ad groups
- **💾 Instant Download** - Ready-to-import CSV, JSON, and reports
- **⚡ Fast Processing** - Optimized for API quota management (50 searches/run)

## 📁 Project Structure
```
AdSmart-AI/
├── 📄 README.md              # Project documentation
├── 📄 requirements.txt       # Python dependencies
├── 🔒 .env.example           # Environment variables template
├── ⚙️ config.example.yaml    # Configuration template
├── 🚫 .gitignore             # Git ignore rules
├── 🚀 main.py                # Core pipeline engine
├── 🌐 app.py                 # Streamlit web interface
└── 📁 src/                   # Source code modules
    ├── 📄 __init__.py
    ├── 🌐 scraper.py         # Website content scraper
    ├── 🔍 keyword_research.py# SERP API keyword research
    ├── 📊 data_processor.py  # Keyword processing & scoring
    ├── 🎯 ad_group_builder.py# Ad group organization
    └── 🤖 llm_helper.py      # OpenAI integration

## 🛠️ Local Setup

### Prerequisites

- **Python 3.8+** installed on your system
- **API Keys** (see API Setup section)
- **Git** (for cloning the repository)

### 1. Clone Repository
git clone https://github.com/yourusername/AdSmart-AI.git
cd AdSmart-AI

### 2. Create Virtual Environment
python -m venv venv
venv\Scripts\activate

### 3. Install Dependencies
pip install -r requirements.txt


### 4. Setup Environment Variables
Create a `.env` file in the project root:
OPENAI_API_KEY=sk-your-openai-api-key-here
SERP_API_KEY=your-serp-api-key-here

### 5. Run the Application
streamlit run app.py


## 📊 Output Files

AdSmart AI generates several file types for different use cases:

### Essential Files
- **`keywords_master.csv`** - Complete keyword list with metrics
- **`keyword_report.md`** - Detailed analysis and insights

### Ad Group Files
- **`ad_group_brand_terms.csv`** - Brand-focused keywords
- **`ad_group_category_terms.csv`** - Product/service keywords
- **`ad_group_location_terms.csv`** - Location-based keywords
- **`ad_group_informational_terms.csv`** - Research intent keywords

### Technical Files
- **`ad_groups_search.json`** - Structured data for API integration
- **`adsmart_ai_keywords.zip`** - All files in one package

## ⚙️ Configuration

### Keyword Settings

## 📈 Performance Tips

1. **Limit keywords** for faster processing (already set to 50)
2. **Use specific seed keywords** for better results
3. **Choose relevant competitors** for quality keyword discovery
4. **Monitor API usage** to stay within quotas

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **OpenAI** for GPT API
- **SERP API** for search data
- **Streamlit** for the web interface
- **Python community** for excellent libraries

## 👨‍💻 Author

**Arpit Mohankar**
- 🚀 AI-Powered SEM Tool Creator
- 💡 Transforming keyword research with artificial intelligence

---

⭐ **Star this repository** if you found it helpful!

📧 **Questions?** Open an issue or reach out!

🚀 **Made with ❤️ and AI**
