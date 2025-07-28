# Unitree G1 Autonomous Mode - Development Plan

## Project Overview
This project implements a fully autonomous navigation system for the Unitree G1 humanoid robot using AI-powered visual analysis through Google Gemini API.

## System Architecture

### Core Components
1. **Camera Module** (`camera_module.py`)
   - OpenCV-based camera capture
   - Image processing and format conversion
   - Base64 encoding for API transmission

2. **AI Vision System** (`ai_vision.py`)
   - Google Gemini API integration
   - Image analysis and decision making
   - Safety analysis capabilities

3. **Robot Control** (`robot_control.py`)
   - Unitree SDK integration
   - Movement command execution
   - Safety monitoring and emergency stop

4. **Autonomous Controller** (`autonomous_mode.py`)
   - Main coordination system
   - Autonomous navigation loop
   - System integration and monitoring

5. **Configuration** (`config.py`)
   - System parameters and limits
   - API configuration
   - Movement command definitions

## Development Phases

### Phase 1: Setup and Dependencies ✅
- [x] Install unitree_sdk2py (Python >=3.8, cyclonedx==0.10.2)
- [x] Install google-generativeai for Gemini API
- [x] Install OpenCV, NumPy, Pillow
- [x] Create project structure

### Phase 2: Core Modules ✅ 
- [x] Implement camera capture with OpenCV
- [x] Create Gemini API integration
- [x] Build movement control system
- [x] Add safety checks and emergency stop

### Phase 3: Integration ✅
- [x] Build autonomous navigation loop
- [x] Integrate all subsystems
- [x] Add comprehensive logging
- [x] Implement error handling

### Phase 4: Testing and Validation
- [ ] Test camera capture functionality
- [ ] Validate Gemini API integration
- [ ] Test movement commands in simulation
- [ ] Perform safety system validation
- [ ] End-to-end system testing

### Phase 5: Deployment
- [ ] Hardware integration testing
- [ ] Performance optimization
- [ ] Real-world validation
- [ ] Documentation completion

## Technical Specifications

### Camera System
- **Interface**: OpenCV cv2.VideoCapture
- **Resolution**: 640x480 (configurable)
- **Format**: RGB/BGR conversion for AI analysis
- **Encoding**: Base64 for API transmission

### AI Integration
- **API**: Google Gemini 1.5-pro vision model
- **Input**: PIL Images with navigation prompts
- **Output**: Structured action commands with reasoning
- **Rate Limiting**: 1 second intervals to manage API costs

### Movement Control
- **SDK**: unitree_sdk2py with DDS communication
- **Commands**: VelocityMove, Turn, StopMove via HighCmd
- **Safety Limits**: 
  - Forward speed: 0.3 m/s max
  - Side speed: 0.2 m/s max  
  - Yaw speed: 0.3 rad/s max

### Safety Features
- Battery level monitoring (>20%)
- Temperature monitoring (<80°C)
- Orientation stability checks
- Emergency stop functionality
- Real-time safety condition validation

## Usage Instructions

### Installation
```bash
python install_dependencies.py
```

### Configuration
1. Set Gemini API key in environment:
   ```bash
   export GEMINI_API_KEY="your_api_key_here"
   ```

2. Modify `config.py` for custom parameters

### Running the System

#### Simulation Mode (No Hardware)
```bash
python autonomous_mode.py --sim
```

#### Hardware Mode
```bash
python autonomous_mode.py
```

#### With Debug Logging
```bash
python autonomous_mode.py --log-level DEBUG
```

### Testing Individual Components
```bash
# Test camera
python camera_module.py

# Test AI vision
python ai_vision.py  

# Test robot control
python robot_control.py
```

## Safety Considerations

### Hardware Safety
- Speed limits enforced at multiple levels
- Continuous balance and orientation monitoring
- Battery and temperature safety checks
- Emergency stop accessible via keyboard interrupt

### AI Safety
- Fallback to stop command if AI fails
- Conservative decision making in uncertain situations
- Human oversight recommended for initial deployments
- Rate limiting to prevent API overload

### Operational Safety
- Always test in simulation first
- Start with reduced speed limits
- Ensure clear operating environment
- Have physical emergency stop available
- Monitor system logs for anomalies

## File Structure
```
G1SA/
├── autonomous_mode.py          # Main autonomous controller
├── camera_module.py            # Camera capture system
├── ai_vision.py               # Gemini API integration  
├── robot_control.py           # Movement control
├── config.py                  # Configuration
├── install_dependencies.py    # Setup script
├── requirements.txt           # Python dependencies
├── development_plan.md        # This file
└── logs/                      # Runtime logs (created automatically)
```

## Logging and Monitoring

### Log Files
- Automatic log file creation with timestamp
- Console output for real-time monitoring
- Detailed debug information available

### Key Metrics
- Frame processing rate
- AI query frequency  
- Movement command execution
- Safety stop events
- System runtime statistics

## Troubleshooting

### Common Issues
1. **Camera not found**: Check camera index in config.py
2. **Gemini API errors**: Verify API key and internet connection
3. **SDK import errors**: Ensure unitree_sdk2py is properly installed
4. **Permission errors**: Check system permissions for camera/hardware access

### Debug Commands
```bash
# Check camera availability
python -c "import cv2; print(cv2.VideoCapture(0).isOpened())"

# Test Gemini API
python -c "import google.generativeai as genai; genai.configure(api_key=os.getenv('GEMINI_API_KEY')); print('API OK')"

# Verify SDK installation
python -c "import unitree_sdk2py; print('SDK OK')"
```

## Future Enhancements

### Potential Improvements
- LiDAR integration for enhanced obstacle detection
- SLAM implementation for mapping
- Path planning algorithms
- Multi-robot coordination
- Voice command interface
- Mobile app for remote monitoring

### Performance Optimization
- GPU acceleration for image processing
- Optimized AI query batching
- Predictive movement planning
- Sensor fusion improvements

## Contributors
- Generated with Claude Code assistant
- Unitree SDK integration
- Google Gemini API implementation