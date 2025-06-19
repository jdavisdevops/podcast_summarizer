# 🎙️ Podcast Transcriber

A Streamlit web application that transcribes podcast episodes from Spotify URLs using OpenAI's Whisper model.

## ✨ Features

- **Easy to use**: Just paste a Spotify episode URL and get a transcript
- **Smart podcast detection**: Automatically finds podcast RSS feeds via iTunes API
- **High-quality transcription**: Uses OpenAI's Whisper model for accurate speech-to-text
- **Download transcripts**: Get your transcripts as downloadable text files
- **Progress tracking**: Real-time progress updates during transcription
- **Error handling**: Helpful error messages and troubleshooting tips

## 🚀 Quick Start

### Local Development

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd podcast-summary
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up Spotify credentials**
   
   Create a `config.json` file:
   ```json
   {
       "spotify_client_id": "your_spotify_client_id",
       "spotify_client_secret": "your_spotify_client_secret"
   }
   ```
   
   Or set environment variables:
   ```bash
   export SPOTIFY_CLIENT_ID="your_spotify_client_id"
   export SPOTIFY_CLIENT_SECRET="your_spotify_client_secret"
   ```

4. **Run the app**
   ```bash
   streamlit run app.py
   ```

5. **Open your browser**
   Navigate to `http://localhost:8501`

### Streamlit Cloud Deployment

1. **Push to GitHub**
   ```bash
   git add .
   git commit -m "Initial commit"
   git push origin main
   ```

2. **Deploy on Streamlit Cloud**
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Connect your GitHub repository
   - Set environment variables for Spotify credentials
   - Deploy!

## 🔧 Configuration

### Spotify API Setup

1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Create a new app
3. Copy the Client ID and Client Secret
4. Add them to your `config.json` or environment variables

### Environment Variables

For production deployment, set these environment variables:

```bash
SPOTIFY_CLIENT_ID=your_client_id
SPOTIFY_CLIENT_SECRET=your_client_secret
```

## 📁 Project Structure

```
podcast-summary/
├── app.py                 # Main Streamlit application
├── collector.py           # Original command-line script
├── config.json           # Spotify credentials (local only)
├── requirements.txt      # Python dependencies
├── .streamlit/
│   └── config.toml      # Streamlit configuration
└── README.md            # This file
```

## 🛠️ How It Works

1. **URL Processing**: Extracts episode ID from Spotify URL
2. **Metadata Retrieval**: Gets episode info from Spotify API
3. **RSS Discovery**: Finds podcast RSS feed via iTunes API
4. **Audio Download**: Downloads audio file from RSS feed
5. **Transcription**: Uses Whisper to convert speech to text
6. **Result Delivery**: Provides transcript for download

## ⚠️ Limitations

- **Free tier constraints**: Streamlit Cloud has 1GB RAM limit
- **CPU-only**: Free tier doesn't support GPU acceleration
- **Processing time**: Longer episodes take more time to transcribe
- **RSS dependency**: Podcast must have a public RSS feed

## 🐛 Troubleshooting

### Common Issues

1. **"Spotify credentials not found"**
   - Check your `config.json` file
   - Verify environment variables are set correctly

2. **"Episode not found in RSS feed"**
   - Try a different episode
   - Check if the podcast has a public RSS feed

3. **"Failed to download audio"**
   - Episode might be premium/exclusive
   - Try a different podcast

4. **Slow transcription**
   - Free tier uses CPU only
   - Consider shorter episodes for testing

## 📝 License

This project is open source and available under the [MIT License](LICENSE).

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📞 Support

If you encounter any issues, please:
1. Check the troubleshooting section above
2. Search existing issues
3. Create a new issue with detailed information 