from flask import Blueprint, request, jsonify
from app.models import SystemSetting
from app.database import session_scope
from app.routes.auth import admin_required

bp = Blueprint('system_settings', __name__, url_prefix='/api/system-settings')

DEFAULT_VIDEO_URL = "https://youtu.be/1nFE78j8Giw?si=w1TYVCKB_CD0jI11"

@bp.route('/video-url', methods=['GET'])
def get_video_url():
    with session_scope() as session:
        setting = session.get(SystemSetting, 'video_url')
        if not setting:
            # Lazy initialization
            setting = SystemSetting(key='video_url', value=DEFAULT_VIDEO_URL)
            session.add(setting)
            session.flush() # Ensure it's saved so we can return the value, commit happens at end of scope
        
        return jsonify({'video_url': setting.value})

@bp.route('/video-url', methods=['PUT'])
@admin_required
def update_video_url():
    data = request.get_json()
    new_url = data.get('video_url')
    
    if not new_url:
        return jsonify({'error': 'Video URL is required'}), 400
        
    with session_scope() as session:
        setting = session.get(SystemSetting, 'video_url')
        if not setting:
            setting = SystemSetting(key='video_url', value=new_url)
            session.add(setting)
        else:
            setting.value = new_url
        
        session.flush()
        return jsonify({'message': 'Video URL updated successfully', 'video_url': setting.value})
