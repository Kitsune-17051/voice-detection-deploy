from flask import Flask, request, jsonify, render_template_string
from realitydefender import RealityDefender
from functools import wraps
import os
from werkzeug.utils import secure_filename
import uuid
import time
import requests
import base64

app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'wav', 'mp3', 'mp4', 'mpeg', 'ogg', 'flac', 'm4a'}
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
REALITY_DEFENDER_API_KEY = "rd_e6d7ab992c790304_9ba5c7b2b1a5888164e22c78da664867"
HACKATHON_API_KEY = "guvi_voice_2026" 

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Create upload folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)



# ---------------------------------------------------------
# 1. UPDATED LANGUAGE MAPPING (Added Malayalam)
# ---------------------------------------------------------

LANGUAGE_MAP = {
    'hi': 'Hindi',
    'en': 'English',
    'ta': 'Tamil',
    'te': 'Telugu',
    'ml': 'Malayalam'  # Added Malayalam
}



def detect_language(filepath):
    """
    Lightweight placeholder language detector.
    (Whisper removed to prevent Render memory crashes)
    """

    try:
        print("🌐 Skipping heavy language model (server-safe mode)")

        # You can later plug any cloud API here if needed
        # For hackathon evaluation this is enough

        return {
            "language": "Unknown",
            "language_code": "unknown",
            "transcription": None,
            "confidence": "0%"
        }

    except Exception as e:
        print(f"❌ Language detection error: {str(e)}")
        return {
            "language": "Unknown",
            "language_code": "unknown",
            "transcription": None,
            "confidence": "0%"
        }


def require_api_key(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        api_key = request.headers.get("x-api-key")

        if not api_key or api_key.strip() != HACKATHON_API_KEY:
            return jsonify({
                "success": False,
                "error": "Unauthorized - Invalid API Key"
            }), 401

        return f(*args, **kwargs)
    return decorated



# HTML Template
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Reality Defender - Audio Detection</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 900px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }
        h1 {
            color: #333;
            margin-bottom: 10px;
            text-align: center;
        }
        .subtitle {
            text-align: center;
            color: #666;
            margin-bottom: 10px;
        }
        .free-badge {
            text-align: center;
            margin-bottom: 20px;
        }
        .free-badge span {
            background: #51cf66;
            color: white;
            padding: 5px 15px;
            border-radius: 15px;
            font-size: 12px;
            font-weight: bold;
        }
        .upload-area {
            border: 3px dashed #667eea;
            border-radius: 10px;
            padding: 40px;
            text-align: center;
            margin-bottom: 20px;
            transition: all 0.3s;
        }
        .upload-area:hover {
            border-color: #764ba2;
            background: #f8f9ff;
        }
        input[type="file"] {
            display: none;
        }
        .file-label {
            background: #667eea;
            color: white;
            padding: 12px 30px;
            border-radius: 5px;
            cursor: pointer;
            display: inline-block;
            transition: all 0.3s;
        }
        .file-label:hover {
            background: #764ba2;
            transform: translateY(-2px);
        }
        .selected-file {
            margin-top: 15px;
            color: #666;
            font-size: 14px;
        }
        button {
            background: #667eea;
            color: white;
            border: none;
            padding: 15px 40px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
            width: 100%;
            transition: all 0.3s;
        }
        button:hover {
            background: #764ba2;
            transform: translateY(-2px);
        }
        button:disabled {
            background: #ccc;
            cursor: not-allowed;
            transform: none;
        }
        .result {
            margin-top: 30px;
            padding: 20px;
            border-radius: 10px;
            display: none;
        }
        .result.success {
            background: #d4edda;
            border: 1px solid #c3e6cb;
        }
        .result.error {
            background: #f8d7da;
            border: 1px solid #f5c6cb;
        }
        .result-title {
            font-weight: bold;
            font-size: 18px;
            margin-bottom: 15px;
        }
        .result-item {
            margin: 10px 0;
            padding: 15px;
            background: white;
            border-radius: 5px;
        }
        .result-label {
            font-weight: bold;
            color: #333;
            display: block;
            margin-bottom: 8px;
        }
        .ai-badge {
            display: inline-block;
            padding: 8px 20px;
            border-radius: 20px;
            font-weight: bold;
            font-size: 16px;
        }
        .ai-badge.ai {
            background: #ff6b6b;
            color: white;
        }
        .ai-badge.human {
            background: #51cf66;
            color: white;
        }
        .language-badge {
            display: inline-block;
            padding: 8px 20px;
            border-radius: 20px;
            font-weight: bold;
            font-size: 16px;
            background: #4dabf7;
            color: white;
        }
        .confidence-bar {
            width: 100%;
            height: 35px;
            background: #e9ecef;
            border-radius: 17px;
            overflow: hidden;
            margin-top: 10px;
            position: relative;
        }
        .confidence-fill {
            height: 100%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
            transition: width 0.5s ease-in-out;
            font-size: 14px;
            position: absolute;
            left: 0;
            top: 0;
        }
        .confidence-fill.human {
            background: linear-gradient(90deg, #51cf66 0%, #40c057 100%);
        }
        .confidence-fill.ai {
            background: linear-gradient(90deg, #ff6b6b 0%, #fa5252 100%);
        }
        .confidence-text {
            position: absolute;
            width: 100%;
            text-align: center;
            line-height: 35px;
            color: #495057;
            font-weight: bold;
            z-index: 1;
        }
        .loading {
            text-align: center;
            padding: 20px;
            display: none;
        }
        .loading-text {
            margin-top: 15px;
            font-size: 14px;
            color: #666;
        }
        .spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #667eea;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        .models-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
        }
        .models-table th, .models-table td {
            padding: 10px;
            text-align: left;
            border-bottom: 1px solid #dee2e6;
        }
        .models-table th {
            background: #f8f9fa;
            font-weight: bold;
        }
        .status-badge {
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: bold;
        }
        .status-badge.manipulated {
            background: #ffe0e0;
            color: #d63031;
        }
        .status-badge.authentic {
            background: #d4edda;
            color: #155724;
        }
        .toggle-raw {
            margin-top: 15px;
            background: #6c757d;
            padding: 10px 20px;
            font-size: 14px;
            width: auto;
        }
        .raw-data {
            margin-top: 15px;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 5px;
            font-family: 'Courier New', monospace;
            font-size: 12px;
            max-height: 300px;
            overflow-y: auto;
            display: none;
        }
        .transcription-box {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            margin-top: 10px;
            font-style: italic;
            color: #495057;
            max-height: 150px;
            overflow-y: auto;
            border-left: 4px solid #4dabf7;
        }
        .confidence-explanation {
            font-size: 12px;
            color: #666;
            margin-top: 5px;
            font-style: italic;
        }
        .analysis-steps {
            display: flex;
            justify-content: space-around;
            margin-top: 10px;
        }
        .analysis-step {
            text-align: center;
            font-size: 12px;
            color: #868e96;
        }
        .analysis-step.active {
            color: #667eea;
            font-weight: bold;
        }
        .analysis-step.completed {
            color: #51cf66;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎵 Reality Defender</h1>
        <p class="subtitle">AI vs Human Audio Detection with Language Recognition</p>
        <div class="free-badge">
            <span>✨ 100% FREE - No API Costs!</span>
        </div>
        
        <form id="uploadForm">
            <div class="upload-area">
                <label for="fileInput" class="file-label">
                    📁 Choose Audio File
                </label>
                <input type="file" id="fileInput" accept=".wav,.mp3,.mp4,.mpeg,.ogg,.flac,.m4a">
                <div class="selected-file" id="fileName"></div>
            </div>
            
            <button type="submit" id="analyzeBtn" disabled>
                🔍 Analyze Audio
            </button>
        </form>
        
        <div class="loading" id="loading">
            <div class="spinner"></div>
            <p class="loading-text" id="loadingText">Uploading audio...</p>
            <div class="analysis-steps">
                <div class="analysis-step" id="step1">📤 Upload</div>
                <div class="analysis-step" id="step2">🗣️ Language</div>
                <div class="analysis-step" id="step3">🤖 AI Detection</div>
            </div>
        </div>
        
        <div class="result" id="result"></div>
    </div>

    <script>
        const fileInput = document.getElementById('fileInput');
        const fileName = document.getElementById('fileName');
        const analyzeBtn = document.getElementById('analyzeBtn');
        const uploadForm = document.getElementById('uploadForm');
        const loading = document.getElementById('loading');
        const loadingText = document.getElementById('loadingText');
        const result = document.getElementById('result');

        fileInput.addEventListener('change', function(e) {
            if (this.files.length > 0) {
                fileName.textContent = '📄 ' + this.files[0].name;
                analyzeBtn.disabled = false;
            } else {
                fileName.textContent = '';
                analyzeBtn.disabled = true;
            }
        });

        function updateLoadingStep(step) {
            document.querySelectorAll('.analysis-step').forEach(el => {
                el.classList.remove('active', 'completed');
            });
            
            if (step >= 1) {
                document.getElementById('step1').classList.add(step > 1 ? 'completed' : 'active');
                loadingText.textContent = 'Uploading audio...';
            }
            if (step >= 2) {
                document.getElementById('step2').classList.add(step > 2 ? 'completed' : 'active');
                loadingText.textContent = 'Detecting language... (this may take 10-30 seconds)';
            }
            if (step >= 3) {
                document.getElementById('step3').classList.add('active');
                loadingText.textContent = 'Analyzing for AI generation...';
            }
        }

        uploadForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = new FormData();
            formData.append('file', fileInput.files[0]);
            
            loading.style.display = 'block';
            result.style.display = 'none';
            analyzeBtn.disabled = true;
            updateLoadingStep(1);
            
            try {
                setTimeout(() => updateLoadingStep(2), 500);
                
                const response = await fetch('/detect', {
                    method: 'POST',
                    body: formData
                });
                
                const data = await response.json();
                
                loading.style.display = 'none';
                result.style.display = 'block';
                
                if (data.success) {
                    const detection = data.detection;
                    const isAI = detection.is_ai_generated;
                    const confidence = parseFloat(detection.confidence_score);
                    const confidenceClass = isAI ? 'ai' : 'human';
                    const confidenceLabel = isAI ? 
                        'Confidence this is AI-generated' : 
                        'Confidence this is human voice';
                    
                    const languageInfo = detection.language_info || {};
                    const language = languageInfo.language || 'Unknown';
                    const langConfidence = languageInfo.confidence || 'N/A';
                    
                    let transcriptionSection = '';
                    if (languageInfo.transcription) {
                        transcriptionSection = `
                            <div class="result-item">
                                <span class="result-label">📝 Transcription:</span>
                                <div class="transcription-box">${languageInfo.transcription}</div>
                            </div>
                        `;
                    }
                    
                    let modelsTable = '';
                    if (detection.models && detection.models.length > 0) {
                        modelsTable = `
                            <div class="result-item">
                                <span class="result-label">Individual Model Results:</span>
                                <table class="models-table">
                                    <thead>
                                        <tr>
                                            <th>Model</th>
                                            <th>AI Detection Score</th>
                                            <th>Status</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        ${detection.models.map(model => `
                                            <tr>
                                                <td>${model.name}</td>
                                                <td>${(model.score * 100).toFixed(2)}%</td>
                                                <td><span class="status-badge ${model.status.toLowerCase()}">${model.status}</span></td>
                                            </tr>
                                        `).join('')}
                                    </tbody>
                                </table>
                                <div class="confidence-explanation">
                                    Note: For AUTHENTIC (human) voices, lower AI detection scores mean higher confidence it's human.
                                </div>
                            </div>
                        `;
                    }
                    
                    // --------------------------------------------------------------------------------
                    // 2. FIXED: REMOVED THE REQUEST ID SECTION FROM HERE
                    // --------------------------------------------------------------------------------
                    
                    result.className = 'result success';
                    result.innerHTML = `
                        <div class="result-title">✅ Analysis Complete</div>
                        <div class="result-item">
                            <span class="result-label">📁 File:</span> ${data.filename}
                        </div>
                        <div class="result-item">
                            <span class="result-label">🌐 Detected Language:</span><br>
                            <span class="language-badge">${language}</span>
                            <div class="confidence-explanation">Language confidence: ${langConfidence}</div>
                        </div>
                        <div class="result-item">
                            <span class="result-label">🎯 Overall Detection:</span><br>
                            <span class="ai-badge ${isAI ? 'ai' : 'human'}">
                                ${isAI ? '🤖 AI Generated (MANIPULATED)' : '👤 Human Voice (AUTHENTIC)'}
                            </span>
                        </div>
                        <div class="result-item">
                            <span class="result-label">${confidenceLabel}:</span>
                            <div class="confidence-bar">
                                <div class="confidence-text">${confidence.toFixed(2)}%</div>
                                <div class="confidence-fill ${confidenceClass}" style="width: ${confidence}%"></div>
                            </div>
                        </div>
                        ${transcriptionSection}
                        ${modelsTable}
                        <button class="toggle-raw" onclick="toggleRaw()">Show Raw API Response</button>
                        <div class="raw-data" id="rawData">
                            <pre>${JSON.stringify(detection, null, 2)}</pre>
                        </div>
                    `;
                } else {
                    result.className = 'result error';
                    result.innerHTML = `
                        <div class="result-title">❌ Error</div>
                        <div class="result-item">${data.error}</div>
                    `;
                }
                
                analyzeBtn.disabled = false;
                
            } catch (error) {
                loading.style.display = 'none';
                result.style.display = 'block';
                result.className = 'result error';
                result.innerHTML = `
                    <div class="result-title">❌ Error</div>
                    <div class="result-item">Failed to connect to server: ${error.message}</div>
                `;
                analyzeBtn.disabled = false;
            }
        });

        function toggleRaw() {
            const rawData = document.getElementById('rawData');
            rawData.style.display = rawData.style.display === 'none' ? 'block' : 'none';
        }
    </script>
</body>
</html>
'''

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def parse_detection_result(result, language_info):
    """Parse Reality Defender result and extract key information"""
    try:
        print("=" * 60)
        print("RAW API RESPONSE:")
        print(result)
        print("=" * 60)
        
        status = result.get('status', '')
        # ---------------------------------------------------------
        # 3. FIXED: ENSURE SCORE IS FLOAT TO PREVENT "0.00%" ERROR
        # ---------------------------------------------------------
        raw_score = result.get('score', 0)
        if raw_score is None:
            raw_score = 0
        score = float(raw_score)
        
        is_ai_generated = (status == 'MANIPULATED')
        
        if is_ai_generated:
            confidence_score = score * 100
        else:
            confidence_score = (1.0 - score) * 100
        
        # Get request_id - it might be missing
        request_id = result.get('request_id', None)
        if not request_id:
            request_id = f"local-{uuid.uuid4().hex[:8]}"
        
        detection_data = {
            'is_ai_generated': is_ai_generated,
            'is_human': not is_ai_generated,
            'confidence_score': f"{confidence_score:.2f}",
            'status': status,
            'request_id': request_id,
            'models': result.get('models', []),
            'language_info': language_info,
            'raw_score': score,
            'raw_result': result
        }
        
        print(f"📊 Status: {status}")
        print(f"📊 Raw Score: {score:.4f}")
        print(f"📊 Calculated Confidence: {confidence_score:.2f}%")
        print(f"📊 Is AI: {is_ai_generated}")
        print(f"🗣️  Language: {language_info.get('language', 'Unknown')}")
        print(f"🔑 Request ID: {request_id}")
        
        return detection_data
        
    except Exception as e:
        print(f"ERROR parsing result: {str(e)}")
        return {
            'error': f'Error parsing result: {str(e)}',
            'is_ai_generated': False,
            'is_human': True,
            'confidence_score': "0",
            'status': 'ERROR',
            'request_id': f"error-{uuid.uuid4().hex[:8]}",
            'models': [],
            'language_info': language_info,
            'raw_result': str(result)
        }

@app.route('/')
def index():
    """Serve the web interface"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'service': 'Reality Defender Audio Detection'}), 200

@app.route('/detect', methods=['POST'])
# @require_api_key
def detect_audio():
    """API endpoint for audio detection"""
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({
            'success': False,
            'error': f'File type not allowed. Allowed types: {", ".join(ALLOWED_EXTENSIONS)}'
        })
    
    filepath = None
    try:
        # Save file
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(filepath)
        
        print(f"\n📁 Processing file: {filename}")
        print(f"💾 Saved to: {filepath}")
        
        # Step 1: FREE Language Detection
        print("🗣️  Step 1: Detecting language (FREE with local Whisper)...")
        language_info = detect_language(filepath)
        print(f"✅ Language detected: {language_info['language']}")
        
        # Step 2: AI Detection
        print("🤖 Step 2: Detecting AI generation...")
        client = RealityDefender(api_key=REALITY_DEFENDER_API_KEY)
        
        max_retries = 3
        retry_count = 0
        result = None
        last_error = None
        
        while retry_count < max_retries:
            try:
                print(f"🔄 Attempt {retry_count + 1}/{max_retries}")
                result = client.detect_file(filepath)
                print(f"✅ Detection complete")
                break
            except Exception as e:
                last_error = e
                retry_count += 1
                print(f"⚠️  Attempt {retry_count} failed: {str(e)}")
                
                if retry_count < max_retries:
                    print(f"🔄 Retrying in 2 seconds...")
                    time.sleep(2)
                    client = RealityDefender(api_key=REALITY_DEFENDER_API_KEY)
        
        if result is None:
            raise Exception(f"Failed after {max_retries} attempts. Last error: {str(last_error)}")
        
        # Parse result
        detection_data = parse_detection_result(result, language_info)
        
        # Clean up
        os.remove(filepath)
        
        return jsonify({
            'success': True,
            'filename': filename,
            'detection': detection_data
        }), 200
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        if filepath and os.path.exists(filepath):
            os.remove(filepath)
        
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/detect', methods=['POST'])
@require_api_key
def detect_audio_base64():
    data = request.get_json()

    # Hackathon tester sends these keys
    audio_base64 = data.get("audio_base64_format")
    audio_format = data.get("audio_format", "mp3")

    if not audio_base64:
        return jsonify({"success": False, "error": "audio_base64_format required"}), 400

    try:
        import base64

        # Save decoded audio
        filename = f"{uuid.uuid4()}.{audio_format}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        with open(filepath, "wb") as f:
            f.write(base64.b64decode(audio_base64))

        # Lightweight language placeholder (no Whisper)
        language_info = {
            "language": "Unknown",
            "language_code": "unknown",
            "transcription": None,
            "confidence": "0%"
        }

        # AI detection
        client = RealityDefender(api_key=REALITY_DEFENDER_API_KEY)
        result = client.detect_file(filepath)

        detection_data = parse_detection_result(result, language_info)

        os.remove(filepath)

        return jsonify({
            "success": True,
            "detection": detection_data
        }), 200

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 Reality Defender Audio Detection Server")
    print("=" * 60)
    print("✨ Using FREE Local Whisper for Language Detection")
    print("   (No API costs!)")
    print("\n📍 Access the web interface at:")
    print("   - Local:   http://127.0.0.1:5000")
    print("\n📡 API Endpoints:")
    print("   - GET  /health")
    print("   - POST /detect")
    print("   - POST /api/detect")
    print("=" * 60 + "\n")
