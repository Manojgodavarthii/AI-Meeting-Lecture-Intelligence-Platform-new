from sqlalchemy import (
    Column, Integer, BigInteger, String, Text, DateTime, Boolean,
    ForeignKey, JSON, Float, SmallInteger, Index, UniqueConstraint, func
)
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.ext.declarative import declared_attr

Base = declarative_base()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  MASTER / LOOKUP TABLES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class Role(Base):
    __tablename__ = "ea_roles"
    id = Column(SmallInteger, primary_key=True, autoincrement=True)
    name = Column(String(64), unique=True, nullable=False)
    description = Column(String(255), default="")
    is_active = Column(Boolean, default=True)

    users = relationship("User", back_populates="role_ref")
    user_roles = relationship("UserRole", back_populates="role_ref")


class Department(Base):
    __tablename__ = "ea_departments"
    id = Column(SmallInteger, primary_key=True, autoincrement=True)
    name = Column(String(128), unique=True, nullable=False)
    code = Column(String(32), unique=True, nullable=True)
    head_user_id = Column(Integer, ForeignKey("ea_users.id", ondelete="SET NULL"), nullable=True)
    is_active = Column(Boolean, default=True)

    members = relationship("User", back_populates="department_ref")
    head = relationship("User", foreign_keys=[head_user_id], post_update=True)


class Team(Base):
    __tablename__ = "ea_teams"
    id = Column(SmallInteger, primary_key=True, autoincrement=True)
    name = Column(String(128), unique=True, nullable=False)
    department_id = Column(SmallInteger, ForeignKey("ea_departments.id", ondelete="SET NULL"), nullable=True)
    lead_user_id = Column(Integer, ForeignKey("ea_users.id", ondelete="SET NULL"), nullable=True)
    is_active = Column(Boolean, default=True)

    department_ref = relationship("Department")
    lead = relationship("User", foreign_keys=[lead_user_id], post_update=True)
    members = relationship("User", back_populates="team_ref")


class StatusMaster(Base):
    __tablename__ = "ea_status_master"
    id = Column(SmallInteger, primary_key=True, autoincrement=True)
    category = Column(String(64), nullable=False, index=True)
    name = Column(String(64), nullable=False)
    color = Column(String(32), default="#8899b0")
    sort_order = Column(SmallInteger, default=0)


class MeetingType(Base):
    __tablename__ = "ea_meeting_types"
    id = Column(SmallInteger, primary_key=True, autoincrement=True)
    name = Column(String(128), unique=True, nullable=False)
    icon = Column(String(64), default="fa-video")
    default_duration = Column(SmallInteger, default=30)


class NotificationType(Base):
    __tablename__ = "ea_notification_types"
    id = Column(SmallInteger, primary_key=True, autoincrement=True)
    name = Column(String(64), unique=True, nullable=False)
    icon = Column(String(64), default="fa-bell")
    color = Column(String(32), default="#818cf8")


class PermissionType(Base):
    __tablename__ = "ea_permission_types"
    id = Column(SmallInteger, primary_key=True, autoincrement=True)
    name = Column(String(64), unique=True, nullable=False)
    code = Column(String(64), unique=True, nullable=False)
    module = Column(String(64), default="general")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  AUTHENTICATION & USERS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class User(Base):
    __tablename__ = "ea_users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(191), unique=True, nullable=False, index=True)
    password_hash = Column(String(512), nullable=False)
    name = Column(String(255), default="")
    display_name = Column(String(255), default="")
    phone = Column(String(64), default="")
    avatar_path = Column(String(512), default="")
    bio = Column(Text, nullable=True)
    role_id = Column(SmallInteger, ForeignKey("ea_roles.id"), nullable=False, default=1, index=True)
    department_id = Column(SmallInteger, ForeignKey("ea_departments.id", ondelete="SET NULL"), nullable=True)
    team_id = Column(SmallInteger, ForeignKey("ea_teams.id", ondelete="SET NULL"), nullable=True)
    is_active = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)
    last_login_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    role_ref = relationship("Role", back_populates="users")
    department_ref = relationship("Department", back_populates="members", foreign_keys=[department_id])
    team_ref = relationship("Team", back_populates="members", foreign_keys=[team_id])

    employee_profile = relationship("EmployeeProfile", back_populates="user", uselist=False)
    student_profile = relationship("StudentProfile", back_populates="user", uselist=False)
    staff_profile = relationship("StaffProfile", back_populates="user", uselist=False)
    admin_profile = relationship("AdminProfile", back_populates="user", uselist=False)
    settings = relationship("UserSetting", back_populates="user", uselist=False)
    profile_links = relationship("ProfileLink", back_populates="user", uselist=False)
    login_history = relationship("LoginHistory", back_populates="user")
    sessions = relationship("UserSession", back_populates="user")
    device_history = relationship("DeviceHistory", back_populates="user")


class UserRole(Base):
    __tablename__ = "ea_user_roles"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("ea_users.id", ondelete="CASCADE"), nullable=False, index=True)
    role_id = Column(SmallInteger, ForeignKey("ea_roles.id"), nullable=False)
    granted_by = Column(Integer, ForeignKey("ea_users.id", ondelete="SET NULL"), nullable=True)
    granted_at = Column(DateTime, server_default=func.now())

    user = relationship("User", foreign_keys=[user_id])
    role_ref = relationship("Role", back_populates="user_roles")
    granted_by_user = relationship("User", foreign_keys=[granted_by])


class EmployeeProfile(Base):
    __tablename__ = "ea_employee_profiles"
    user_id = Column(Integer, ForeignKey("ea_users.id", ondelete="CASCADE"), primary_key=True)
    job_title = Column(String(128), default="")
    company = Column(String(255), default="")
    employee_id = Column(String(64), unique=True, nullable=True)
    manager_user_id = Column(Integer, ForeignKey("ea_users.id", ondelete="SET NULL"), nullable=True)
    date_of_joining = Column(DateTime, nullable=True)
    employment_type = Column(String(32), default="full_time")
    work_location = Column(String(128), default="")

    user = relationship("User", back_populates="employee_profile")
    manager = relationship("User", foreign_keys=[manager_user_id], post_update=True)


class StudentProfile(Base):
    __tablename__ = "ea_student_profiles"
    user_id = Column(Integer, ForeignKey("ea_users.id", ondelete="CASCADE"), primary_key=True)
    student_id = Column(String(64), unique=True, nullable=True)
    course = Column(String(128), default="")
    semester = Column(String(16), default="")
    year_of_study = Column(SmallInteger, default=1)
    advisor_user_id = Column(Integer, ForeignKey("ea_users.id", ondelete="SET NULL"), nullable=True)
    enrollment_date = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="student_profile")
    advisor = relationship("User", foreign_keys=[advisor_user_id], post_update=True)


class StaffProfile(Base):
    __tablename__ = "ea_staff_profiles"
    user_id = Column(Integer, ForeignKey("ea_users.id", ondelete="CASCADE"), primary_key=True)
    staff_id = Column(String(64), unique=True, nullable=True)
    designation = Column(String(128), default="")
    shift = Column(String(32), default="general")
    supervisor_user_id = Column(Integer, ForeignKey("ea_users.id", ondelete="SET NULL"), nullable=True)

    user = relationship("User", back_populates="staff_profile")
    supervisor = relationship("User", foreign_keys=[supervisor_user_id], post_update=True)


class AdminProfile(Base):
    __tablename__ = "ea_admin_profiles"
    user_id = Column(Integer, ForeignKey("ea_users.id", ondelete="CASCADE"), primary_key=True)
    access_level = Column(String(32), default="admin")
    mfa_enabled = Column(Boolean, default=False)
    session_timeout_min = Column(SmallInteger, default=30)
    ip_whitelist = Column(JSON, nullable=True)

    user = relationship("User", back_populates="admin_profile")


class LoginHistory(Base):
    __tablename__ = "ea_login_history"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("ea_users.id", ondelete="CASCADE"), nullable=False, index=True)
    device_name = Column(String(255), default="")
    ip_address = Column(String(64), default="")
    user_agent = Column(Text, nullable=True)
    login_time = Column(DateTime, server_default=func.now(), index=True)
    success = Column(Boolean, default=True)
    session_id = Column(String(128), nullable=True)

    user = relationship("User", back_populates="login_history")

    __table_args__ = (
        Index("idx_login_history_user_time", "user_id", "login_time"),
    )


class LoginHistoryArchive(Base):
    __tablename__ = "ea_login_history_archive"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True)
    device_name = Column(String(255), default="")
    ip_address = Column(String(64), default="")
    user_agent = Column(Text, nullable=True)
    login_time = Column(DateTime, index=True)
    success = Column(Boolean, default=True)
    session_id = Column(String(128), nullable=True)
    archived_at = Column(DateTime, server_default=func.now())


class UserSession(Base):
    __tablename__ = "ea_user_sessions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("ea_users.id", ondelete="CASCADE"), nullable=False, index=True)
    token = Column(String(512), unique=True, nullable=False)
    ip_address = Column(String(64), default="")
    device_info = Column(String(255), default="")
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="sessions")


class UserSetting(Base):
    __tablename__ = "ea_user_settings"
    user_id = Column(Integer, ForeignKey("ea_users.id", ondelete="CASCADE"), primary_key=True)
    theme = Column(String(32), default="dark")
    language = Column(String(16), default="en")
    timezone = Column(String(64), default="UTC")
    notification_prefs = Column(JSON, nullable=True)
    privacy_settings = Column(JSON, nullable=True)
    updated_at = Column(DateTime, onupdate=func.now())

    user = relationship("User", back_populates="settings")


class ProfileLink(Base):
    __tablename__ = "ea_profile_links"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("ea_users.id", ondelete="CASCADE"), nullable=False, index=True)
    link_key = Column(String(128), unique=True, nullable=False, index=True)
    department = Column(String(128), default="")
    display_name = Column(String(255), default="")
    allow_follow = Column(Boolean, default=True)
    visibility = Column(JSON, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="profile_links")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  MEETINGS MODULE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class Meeting(Base):
    __tablename__ = "ea_meetings"
    id = Column(Integer, primary_key=True, autoincrement=True)
    host_user_id = Column(Integer, ForeignKey("ea_users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    meeting_type_id = Column(SmallInteger, ForeignKey("ea_meeting_types.id", ondelete="SET NULL"), nullable=True)
    status_id = Column(SmallInteger, ForeignKey("ea_status_master.id", ondelete="SET NULL"), nullable=True, index=True)
    scheduled_date = Column(DateTime, nullable=False, index=True)
    duration_minutes = Column(SmallInteger, default=30)
    timezone = Column(String(64), default="UTC")
    location = Column(String(255), default="")
    agenda = Column(Text, nullable=True)
    meeting_score = Column(Float, default=80.0)
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    host = relationship("User", foreign_keys=[host_user_id])
    meeting_type = relationship("MeetingType")
    status = relationship("StatusMaster")
    participants = relationship("MeetingParticipant", back_populates="meeting")
    recordings = relationship("MeetingRecording", back_populates="meeting")
    transcripts = relationship("MeetingTranscript", back_populates="meeting")
    summary = relationship("MeetingSummary", back_populates="meeting", uselist=False)
    action_items = relationship("MeetingActionItem", back_populates="meeting")
    replay = relationship("MeetingReplay", back_populates="meeting", uselist=False)
    tags = relationship("MeetingTag", back_populates="meeting")
    feedback = relationship("MeetingFeedback", back_populates="meeting")
    ai_insights = relationship("MeetingAIInsight", back_populates="meeting")

    __table_args__ = (
        Index("idx_meetings_host_date", "host_user_id", "scheduled_date"),
    )


class MeetingParticipant(Base):
    __tablename__ = "ea_meeting_participants"
    id = Column(Integer, primary_key=True, autoincrement=True)
    meeting_id = Column(Integer, ForeignKey("ea_meetings.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("ea_users.id", ondelete="CASCADE"), nullable=False)
    status_id = Column(SmallInteger, ForeignKey("ea_status_master.id", ondelete="SET NULL"), nullable=True)
    rsvp_status = Column(String(32), default="pending")
    attended = Column(Boolean, default=False)
    joined_at = Column(DateTime, nullable=True)
    left_at = Column(DateTime, nullable=True)

    meeting = relationship("Meeting", back_populates="participants")
    user = relationship("User")

    __table_args__ = (
        UniqueConstraint("meeting_id", "user_id", name="uq_meeting_participant"),
    )


class MeetingRecording(Base):
    __tablename__ = "ea_meeting_recordings"
    id = Column(Integer, primary_key=True, autoincrement=True)
    meeting_id = Column(Integer, ForeignKey("ea_meetings.id", ondelete="CASCADE"), nullable=False, index=True)
    file_path = Column(String(512), nullable=False)
    storage_provider = Column(String(64), default="local")
    file_size_bytes = Column(BigInteger, default=0)
    mime_type = Column(String(64), default="audio/mp4")
    duration_sec = Column(Integer, default=0)
    processed = Column(Boolean, default=False)
    uploaded_at = Column(DateTime, server_default=func.now())

    meeting = relationship("Meeting", back_populates="recordings")


class MeetingRecordingArchive(Base):
    __tablename__ = "ea_meeting_recordings_archive"
    id = Column(Integer, primary_key=True, autoincrement=True)
    meeting_id = Column(Integer, nullable=False, index=True)
    file_path = Column(String(512), nullable=False)
    storage_provider = Column(String(64), default="local")
    file_size_bytes = Column(BigInteger, default=0)
    mime_type = Column(String(64), default="audio/mp4")
    duration_sec = Column(Integer, default=0)
    archived_at = Column(DateTime, server_default=func.now())


class MeetingTranscript(Base):
    __tablename__ = "ea_meeting_transcripts"
    id = Column(Integer, primary_key=True, autoincrement=True)
    meeting_id = Column(Integer, ForeignKey("ea_meetings.id", ondelete="CASCADE"), nullable=False, index=True)
    content = Column(Text, nullable=False)
    language = Column(String(16), default="en")
    word_count = Column(Integer, default=0)
    speaker_diarization = Column(JSON, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    meeting = relationship("Meeting", back_populates="transcripts")


class MeetingTranscriptArchive(Base):
    __tablename__ = "ea_meeting_transcripts_archive"
    id = Column(Integer, primary_key=True, autoincrement=True)
    meeting_id = Column(Integer, nullable=False, index=True)
    content = Column(Text, nullable=False)
    language = Column(String(16), default="en")
    word_count = Column(Integer, default=0)
    speaker_diarization = Column(JSON, nullable=True)
    archived_at = Column(DateTime, server_default=func.now())


class MeetingSummary(Base):
    __tablename__ = "ea_meeting_summaries"
    meeting_id = Column(Integer, ForeignKey("ea_meetings.id", ondelete="CASCADE"), primary_key=True)
    overview = Column(Text, nullable=True)
    key_points = Column(JSON, nullable=True)
    decisions = Column(JSON, nullable=True)
    ai_generated = Column(Boolean, default=True)
    generated_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    meeting = relationship("Meeting", back_populates="summary")


class MeetingActionItem(Base):
    __tablename__ = "ea_meeting_action_items"
    id = Column(Integer, primary_key=True, autoincrement=True)
    meeting_id = Column(Integer, ForeignKey("ea_meetings.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    assignee_user_id = Column(Integer, ForeignKey("ea_users.id", ondelete="SET NULL"), nullable=True)
    priority = Column(String(16), default="medium")
    due_date = Column(DateTime, nullable=True)
    status_id = Column(SmallInteger, ForeignKey("ea_status_master.id", ondelete="SET NULL"), nullable=True)
    is_completed = Column(Boolean, default=False)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    meeting = relationship("Meeting", back_populates="action_items")
    assignee = relationship("User")

    __table_args__ = (
        Index("idx_action_item_meeting_assignee", "meeting_id", "assignee_user_id"),
    )


class MeetingReplay(Base):
    __tablename__ = "ea_meeting_replays"
    meeting_id = Column(Integer, ForeignKey("ea_meetings.id", ondelete="CASCADE"), primary_key=True)
    replay_data = Column(JSON, nullable=True)
    highlights = Column(JSON, nullable=True)
    replay_count = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    meeting = relationship("Meeting", back_populates="replay")


class MeetingTag(Base):
    __tablename__ = "ea_meeting_tags"
    id = Column(Integer, primary_key=True, autoincrement=True)
    meeting_id = Column(Integer, ForeignKey("ea_meetings.id", ondelete="CASCADE"), nullable=False, index=True)
    tag = Column(String(64), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    meeting = relationship("Meeting", back_populates="tags")

    __table_args__ = (
        UniqueConstraint("meeting_id", "tag", name="uq_meeting_tag"),
        Index("idx_meeting_tag", "tag"),
    )


class MeetingFeedback(Base):
    __tablename__ = "ea_meeting_feedback"
    id = Column(Integer, primary_key=True, autoincrement=True)
    meeting_id = Column(Integer, ForeignKey("ea_meetings.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("ea_users.id", ondelete="CASCADE"), nullable=False)
    rating = Column(SmallInteger, default=5)
    comments = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    meeting = relationship("Meeting", back_populates="feedback")
    user = relationship("User")

    __table_args__ = (
        UniqueConstraint("meeting_id", "user_id", name="uq_meeting_feedback"),
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  COMMUNICATION MODULE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class Conversation(Base):
    __tablename__ = "ea_conversations"
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), default="")
    conversation_type = Column(String(32), default="direct")
    created_by = Column(Integer, ForeignKey("ea_users.id", ondelete="SET NULL"), nullable=True)
    is_group = Column(Boolean, default=False)
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    members = relationship("ConversationMember", back_populates="conversation")
    messages = relationship("Message", back_populates="conversation")


class ConversationMember(Base):
    __tablename__ = "ea_conversation_members"
    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(Integer, ForeignKey("ea_conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("ea_users.id", ondelete="CASCADE"), nullable=False)
    last_read_at = Column(DateTime, nullable=True)
    is_muted = Column(Boolean, default=False)
    joined_at = Column(DateTime, server_default=func.now())

    conversation = relationship("Conversation", back_populates="members")
    user = relationship("User")

    __table_args__ = (
        UniqueConstraint("conversation_id", "user_id", name="uq_conversation_member"),
    )


class Message(Base):
    __tablename__ = "ea_messages"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    conversation_id = Column(Integer, ForeignKey("ea_conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    sender_id = Column(Integer, ForeignKey("ea_users.id", ondelete="CASCADE"), nullable=False, index=True)
    body = Column(Text, nullable=True)
    message_type = Column(String(32), default="text")
    is_deleted = Column(Boolean, default=False)
    sent_at = Column(DateTime, server_default=func.now(), index=True)
    edited_at = Column(DateTime, nullable=True)

    conversation = relationship("Conversation", back_populates="messages")
    sender = relationship("User")
    attachments = relationship("MessageAttachment", back_populates="message")

    __table_args__ = (
        Index("idx_messages_conversation_sent", "conversation_id", "sent_at"),
    )


class MessageAttachment(Base):
    __tablename__ = "ea_message_attachments"
    id = Column(Integer, primary_key=True, autoincrement=True)
    message_id = Column(BigInteger, ForeignKey("ea_messages.id", ondelete="CASCADE"), nullable=False, index=True)
    file_path = Column(String(512), nullable=False)
    storage_provider = Column(String(64), default="local")
    filename = Column(String(255), nullable=False)
    mime_type = Column(String(64), default="")
    file_size_bytes = Column(BigInteger, default=0)
    uploaded_at = Column(DateTime, server_default=func.now())

    message = relationship("Message", back_populates="attachments")


class Notification(Base):
    __tablename__ = "ea_notifications"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("ea_users.id", ondelete="CASCADE"), nullable=False, index=True)
    type_id = Column(SmallInteger, ForeignKey("ea_notification_types.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(255), nullable=False)
    body = Column(Text, nullable=True)
    link = Column(String(512), nullable=True)
    is_read = Column(Boolean, default=False)
    read_at = Column(DateTime, nullable=True)
    is_archived = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now(), index=True)

    user = relationship("User")

    __table_args__ = (
        Index("idx_notifications_user_read", "user_id", "is_read", "created_at"),
    )


class NotificationArchive(Base):
    __tablename__ = "ea_notifications_archive"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True)
    type_id = Column(SmallInteger, nullable=True)
    title = Column(String(255), nullable=False)
    body = Column(Text, nullable=True)
    link = Column(String(512), nullable=True)
    is_read = Column(Boolean, default=False)
    archived_at = Column(DateTime, server_default=func.now(), index=True)


class Announcement(Base):
    __tablename__ = "ea_announcements"
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    body = Column(Text, nullable=True)
    created_by = Column(Integer, ForeignKey("ea_users.id", ondelete="SET NULL"), nullable=True)
    target_role_id = Column(SmallInteger, ForeignKey("ea_roles.id", ondelete="SET NULL"), nullable=True)
    priority = Column(String(16), default="normal")
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    creator = relationship("User")
    target_role = relationship("Role")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  CALENDAR MODULE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class CalendarEvent(Base):
    __tablename__ = "ea_calendar_events"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("ea_users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    event_date = Column(DateTime, nullable=False, index=True)
    end_date = Column(DateTime, nullable=True)
    event_type = Column(String(32), default="event")
    color = Column(String(32), default="#818cf8")
    is_all_day = Column(Boolean, default=False)
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    user = relationship("User")
    attendees = relationship("CalendarAttendee", back_populates="event")

    __table_args__ = (
        Index("idx_calendar_user_date", "user_id", "event_date"),
    )


class CalendarAttendee(Base):
    __tablename__ = "ea_calendar_attendees"
    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(Integer, ForeignKey("ea_calendar_events.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("ea_users.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(32), default="pending")

    event = relationship("CalendarEvent", back_populates="attendees")
    user = relationship("User")

    __table_args__ = (
        UniqueConstraint("event_id", "user_id", name="uq_calendar_attendee"),
    )


class Holiday(Base):
    __tablename__ = "ea_holidays"
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    date = Column(DateTime, nullable=False, index=True)
    type = Column(String(32), default="public")
    is_recurring = Column(Boolean, default=False)
    created_by = Column(Integer, ForeignKey("ea_users.id", ondelete="SET NULL"), nullable=True)


class Reminder(Base):
    __tablename__ = "ea_reminders"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("ea_users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    remind_at = Column(DateTime, nullable=False, index=True)
    is_sent = Column(Boolean, default=False)
    sent_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  PROJECTS & TASKS MODULE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class Project(Base):
    __tablename__ = "ea_projects"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status_id = Column(SmallInteger, ForeignKey("ea_status_master.id", ondelete="SET NULL"), nullable=True, index=True)
    department_id = Column(SmallInteger, ForeignKey("ea_departments.id", ondelete="SET NULL"), nullable=True)
    owner_user_id = Column(Integer, ForeignKey("ea_users.id", ondelete="SET NULL"), nullable=True)
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    priority = Column(String(16), default="medium")
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    owner = relationship("User", foreign_keys=[owner_user_id])
    members = relationship("ProjectMember", back_populates="project")
    tasks = relationship("Task", back_populates="project")
    documents = relationship("ProjectDocument", back_populates="project")
    reports = relationship("ProjectReport", back_populates="project")
    health_log = relationship("ProjectHealth", back_populates="project")
    risks = relationship("ProjectRisk", back_populates="project")


class ProjectMember(Base):
    __tablename__ = "ea_project_members"
    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("ea_projects.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("ea_users.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(32), default="member")
    joined_at = Column(DateTime, server_default=func.now())

    project = relationship("Project", back_populates="members")
    user = relationship("User")

    __table_args__ = (
        UniqueConstraint("project_id", "user_id", name="uq_project_member"),
    )


class Task(Base):
    __tablename__ = "ea_tasks"
    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("ea_projects.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    assignee_user_id = Column(Integer, ForeignKey("ea_users.id", ondelete="SET NULL"), nullable=True)
    status_id = Column(SmallInteger, ForeignKey("ea_status_master.id", ondelete="SET NULL"), nullable=True, index=True)
    priority = Column(String(16), default="medium")
    due_date = Column(DateTime, nullable=True)
    is_completed = Column(Boolean, default=False)
    completed_at = Column(DateTime, nullable=True)
    estimated_hours = Column(Float, nullable=True)
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    project = relationship("Project", back_populates="tasks")
    assignee = relationship("User")
    comments = relationship("TaskComment", back_populates="task")

    __table_args__ = (
        Index("idx_tasks_project_status", "project_id", "status_id"),
    )


class TaskComment(Base):
    __tablename__ = "ea_task_comments"
    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("ea_tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("ea_users.id", ondelete="SET NULL"), nullable=True)
    body = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    task = relationship("Task", back_populates="comments")
    user = relationship("User")


class ProjectDocument(Base):
    __tablename__ = "ea_project_documents"
    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("ea_projects.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=False)
    storage_provider = Column(String(64), default="local")
    file_size_bytes = Column(BigInteger, default=0)
    uploaded_by = Column(Integer, ForeignKey("ea_users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    project = relationship("Project", back_populates="documents")
    uploader = relationship("User")


class ProjectReport(Base):
    __tablename__ = "ea_project_reports"
    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("ea_projects.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=True)
    type = Column(String(32), default="weekly")
    generated_by = Column(Integer, ForeignKey("ea_users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    project = relationship("Project", back_populates="reports")
    generator = relationship("User")


class ProjectHealth(Base):
    __tablename__ = "ea_project_health"
    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("ea_projects.id", ondelete="CASCADE"), nullable=False, index=True)
    health_status = Column(String(32), default="on_track")
    metrics = Column(JSON, nullable=True)
    notes = Column(Text, nullable=True)
    recorded_by = Column(Integer, ForeignKey("ea_users.id", ondelete="SET NULL"), nullable=True)
    recorded_at = Column(DateTime, server_default=func.now())

    project = relationship("Project", back_populates="health_log")


class ProjectRisk(Base):
    __tablename__ = "ea_project_risks"
    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("ea_projects.id", ondelete="CASCADE"), nullable=False, index=True)
    description = Column(Text, nullable=False)
    impact = Column(String(32), default="medium")
    probability = Column(String(32), default="medium")
    mitigation = Column(Text, nullable=True)
    status_id = Column(SmallInteger, ForeignKey("ea_status_master.id", ondelete="SET NULL"), nullable=True)
    raised_by = Column(Integer, ForeignKey("ea_users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    project = relationship("Project", back_populates="risks")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  AI MODULE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class AIChatHistory(Base):
    __tablename__ = "ea_ai_chat_history"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("ea_users.id", ondelete="CASCADE"), nullable=False, index=True)
    session_id = Column(String(128), index=True, nullable=True)
    role = Column(String(16), nullable=False)
    content = Column(Text, nullable=False)
    tokens_used = Column(Integer, default=0)
    model = Column(String(64), default="default")
    created_at = Column(DateTime, server_default=func.now(), index=True)

    user = relationship("User")

    __table_args__ = (
        Index("idx_ai_chat_user_session", "user_id", "session_id"),
    )


class AIChatHistoryArchive(Base):
    __tablename__ = "ea_ai_chat_history_archive"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True)
    session_id = Column(String(128), nullable=True)
    role = Column(String(16), nullable=False)
    content = Column(Text, nullable=False)
    tokens_used = Column(Integer, default=0)
    model = Column(String(64), default="default")
    archived_at = Column(DateTime, server_default=func.now(), index=True)


class AICommand(Base):
    __tablename__ = "ea_ai_commands"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("ea_users.id", ondelete="CASCADE"), nullable=False, index=True)
    command = Column(String(255), nullable=False)
    response = Column(Text, nullable=True)
    module = Column(String(64), default="general")
    execution_time_ms = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())


class KnowledgeCategory(Base):
    __tablename__ = "ea_knowledge_categories"
    id = Column(SmallInteger, primary_key=True, autoincrement=True)
    name = Column(String(128), unique=True, nullable=False)
    icon = Column(String(64), default="fa-book")
    parent_id = Column(SmallInteger, ForeignKey("ea_knowledge_categories.id"), nullable=True)
    sort_order = Column(SmallInteger, default=0)
    is_active = Column(Boolean, default=True)

    parent = relationship("KnowledgeCategory", remote_side=[id])


class KnowledgeDocument(Base):
    __tablename__ = "ea_knowledge_documents"
    id = Column(Integer, primary_key=True, autoincrement=True)
    category_id = Column(SmallInteger, ForeignKey("ea_knowledge_categories.id", ondelete="SET NULL"), nullable=True, index=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=True)
    file_path = Column(String(512), nullable=True)
    tags = Column(JSON, nullable=True)
    is_published = Column(Boolean, default=True)
    uploaded_by = Column(Integer, ForeignKey("ea_users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    uploader = relationship("User")


class OrganizationBrain(Base):
    __tablename__ = "ea_organization_brain"
    id = Column(Integer, primary_key=True, autoincrement=True)
    entity_type = Column(String(64), nullable=False)
    entity_id = Column(Integer, nullable=False, index=True)
    key = Column(String(128), nullable=False)
    value = Column(Text, nullable=True)
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("entity_type", "entity_id", "key", name="uq_brain_entity_key"),
    )


class MeetingAIInsight(Base):
    __tablename__ = "ea_meeting_ai_insights"
    id = Column(Integer, primary_key=True, autoincrement=True)
    meeting_id = Column(Integer, ForeignKey("ea_meetings.id", ondelete="CASCADE"), nullable=False, index=True)
    insight_type = Column(String(64), nullable=False)
    content = Column(Text, nullable=False)
    confidence = Column(Float, default=0.0)
    created_at = Column(DateTime, server_default=func.now())

    meeting = relationship("Meeting", back_populates="ai_insights")

    __table_args__ = (
        Index("idx_ai_insight_meeting_type", "meeting_id", "insight_type"),
    )


class SearchHistory(Base):
    __tablename__ = "ea_search_history"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("ea_users.id", ondelete="CASCADE"), nullable=False, index=True)
    query = Column(String(255), nullable=False)
    result_count = Column(Integer, default=0)
    search_type = Column(String(32), default="general")
    created_at = Column(DateTime, server_default=func.now(), index=True)

    user = relationship("User")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  ANALYTICS MODULE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class DashboardMetric(Base):
    __tablename__ = "ea_dashboard_metrics"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("ea_users.id", ondelete="CASCADE"), nullable=False, index=True)
    metric_key = Column(String(128), nullable=False)
    metric_value = Column(JSON, nullable=False)
    period = Column(String(32), default="daily")
    recorded_at = Column(DateTime, server_default=func.now())

    user = relationship("User")

    __table_args__ = (
        UniqueConstraint("user_id", "metric_key", "period", name="uq_dashboard_metric"),
    )


class AnalyticsCache(Base):
    __tablename__ = "ea_analytics_cache"
    id = Column(Integer, primary_key=True, autoincrement=True)
    cache_key = Column(String(255), unique=True, nullable=False, index=True)
    cache_data = Column(JSON, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, server_default=func.now())


class HistoricalStatistic(Base):
    __tablename__ = "ea_historical_statistics"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    stat_key = Column(String(128), nullable=False, index=True)
    stat_value = Column(JSON, nullable=False)
    period = Column(String(32), nullable=False)
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    recorded_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        Index("idx_historical_stat_lookup", "stat_key", "period_start", "period_end"),
    )


class ReportHistory(Base):
    __tablename__ = "ea_report_history"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("ea_users.id", ondelete="SET NULL"), nullable=True)
    report_type = Column(String(64), nullable=False)
    parameters = Column(JSON, nullable=True)
    file_path = Column(String(512), nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  SUPPORT MODULE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class Query(Base):
    __tablename__ = "ea_queries"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("ea_users.id", ondelete="CASCADE"), nullable=False, index=True)
    subject = Column(String(255), nullable=False)
    message = Column(Text, nullable=True)
    category = Column(String(64), default="general")
    status_id = Column(SmallInteger, ForeignKey("ea_status_master.id", ondelete="SET NULL"), nullable=True, index=True)
    assigned_to = Column(Integer, ForeignKey("ea_users.id", ondelete="SET NULL"), nullable=True)
    priority = Column(String(16), default="normal")
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    user = relationship("User", foreign_keys=[user_id])
    assignee = relationship("User", foreign_keys=[assigned_to])


class Ticket(Base):
    __tablename__ = "ea_tickets"
    id = Column(Integer, primary_key=True, autoincrement=True)
    query_id = Column(Integer, ForeignKey("ea_queries.id", ondelete="SET NULL"), nullable=True)
    user_id = Column(Integer, ForeignKey("ea_users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(64), default="technical")
    priority = Column(String(16), default="medium")
    status_id = Column(SmallInteger, ForeignKey("ea_status_master.id", ondelete="SET NULL"), nullable=True, index=True)
    assigned_to = Column(Integer, ForeignKey("ea_users.id", ondelete="SET NULL"), nullable=True)
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    user = relationship("User", foreign_keys=[user_id])
    assignee = relationship("User", foreign_keys=[assigned_to])
    comments = relationship("TicketComment", back_populates="ticket")
    attachments = relationship("TicketAttachment", back_populates="ticket")


class TicketComment(Base):
    __tablename__ = "ea_ticket_comments"
    id = Column(Integer, primary_key=True, autoincrement=True)
    ticket_id = Column(Integer, ForeignKey("ea_tickets.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("ea_users.id", ondelete="SET NULL"), nullable=True)
    body = Column(Text, nullable=False)
    is_internal = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())

    ticket = relationship("Ticket", back_populates="comments")
    user = relationship("User")


class TicketAttachment(Base):
    __tablename__ = "ea_ticket_attachments"
    id = Column(Integer, primary_key=True, autoincrement=True)
    ticket_id = Column(Integer, ForeignKey("ea_tickets.id", ondelete="CASCADE"), nullable=False, index=True)
    file_path = Column(String(512), nullable=False)
    filename = Column(String(255), nullable=False)
    mime_type = Column(String(64), default="")
    file_size_bytes = Column(BigInteger, default=0)
    uploaded_by = Column(Integer, ForeignKey("ea_users.id", ondelete="SET NULL"), nullable=True)
    uploaded_at = Column(DateTime, server_default=func.now())

    ticket = relationship("Ticket", back_populates="attachments")


class UserRequest(Base):
    __tablename__ = "ea_user_requests"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("ea_users.id", ondelete="CASCADE"), nullable=False, index=True)
    request_type = Column(String(64), nullable=False)
    description = Column(Text, nullable=True)
    status_id = Column(SmallInteger, ForeignKey("ea_status_master.id", ondelete="SET NULL"), nullable=True, index=True)
    reviewed_by = Column(Integer, ForeignKey("ea_users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    user = relationship("User", foreign_keys=[user_id])
    reviewer = relationship("User", foreign_keys=[reviewed_by])


class Feedback(Base):
    __tablename__ = "ea_feedback"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("ea_users.id", ondelete="SET NULL"), nullable=True)
    rating = Column(SmallInteger, default=5)
    message = Column(Text, nullable=True)
    category = Column(String(64), default="general")
    created_at = Column(DateTime, server_default=func.now())


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  SECURITY MODULE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class SecurityEvent(Base):
    __tablename__ = "ea_security_events"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("ea_users.id", ondelete="SET NULL"), nullable=True, index=True)
    event_type = Column(String(64), nullable=False, index=True)
    ip_address = Column(String(64), default="")
    details = Column(JSON, nullable=True)
    severity = Column(String(16), default="info")
    source = Column(String(64), default="system")
    created_at = Column(DateTime, server_default=func.now(), index=True)

    user = relationship("User")

    __table_args__ = (
        Index("idx_security_events_type_time", "event_type", "created_at"),
    )


class SecurityEventArchive(Base):
    __tablename__ = "ea_security_events_archive"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=True, index=True)
    event_type = Column(String(64), nullable=False)
    ip_address = Column(String(64), default="")
    details = Column(JSON, nullable=True)
    severity = Column(String(16), default="info")
    source = Column(String(64), default="system")
    archived_at = Column(DateTime, server_default=func.now(), index=True)


class FailedLogin(Base):
    __tablename__ = "ea_failed_logins"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    email = Column(String(191), nullable=False, index=True)
    ip_address = Column(String(64), default="")
    attempt_time = Column(DateTime, server_default=func.now(), index=True)
    reason = Column(String(64), default="invalid_password")


class BlockedDevice(Base):
    __tablename__ = "ea_blocked_devices"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("ea_users.id", ondelete="CASCADE"), nullable=False, index=True)
    device_fingerprint = Column(String(255), nullable=False)
    device_name = Column(String(255), default="")
    reason = Column(String(255), default="")
    blocked_by = Column(Integer, ForeignKey("ea_users.id", ondelete="SET NULL"), nullable=True)
    blocked_at = Column(DateTime, server_default=func.now())
    is_active = Column(Boolean, default=True)

    user = relationship("User", foreign_keys=[user_id])
    blocker = relationship("User", foreign_keys=[blocked_by])


class DeviceHistory(Base):
    __tablename__ = "ea_device_history"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("ea_users.id", ondelete="CASCADE"), nullable=False, index=True)
    device_fingerprint = Column(String(255), nullable=False)
    device_name = Column(String(255), default="")
    ip_address = Column(String(64), default="")
    user_agent = Column(Text, nullable=True)
    first_seen = Column(DateTime, server_default=func.now())
    last_seen = Column(DateTime, server_default=func.now(), onupdate=func.now())
    is_trusted = Column(Boolean, default=False)

    user = relationship("User", back_populates="device_history")


class AccessLog(Base):
    __tablename__ = "ea_access_logs"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("ea_users.id", ondelete="SET NULL"), nullable=True, index=True)
    action = Column(String(128), nullable=False)
    resource = Column(String(255), nullable=True)
    ip_address = Column(String(64), default="")
    user_agent = Column(Text, nullable=True)
    success = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now(), index=True)

    user = relationship("User")


class SecuritySetting(Base):
    __tablename__ = "ea_security_settings"
    id = Column(Integer, primary_key=True, autoincrement=True)
    setting_key = Column(String(128), unique=True, nullable=False)
    setting_value = Column(JSON, nullable=False)
    description = Column(String(255), default="")
    updated_by = Column(Integer, ForeignKey("ea_users.id", ondelete="SET NULL"), nullable=True)
    updated_at = Column(DateTime, onupdate=func.now())


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  ADMINISTRATION MODULE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class Organization(Base):
    __tablename__ = "ea_organizations"
    id = Column(SmallInteger, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    code = Column(String(32), unique=True, nullable=True)
    domain = Column(String(255), nullable=True)
    logo_path = Column(String(512), nullable=True)
    contact_email = Column(String(191), default="")
    contact_phone = Column(String(64), default="")
    address = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())


class SystemSetting(Base):
    __tablename__ = "ea_system_settings"
    id = Column(Integer, primary_key=True, autoincrement=True)
    setting_key = Column(String(128), unique=True, nullable=False)
    setting_value = Column(JSON, nullable=False)
    module = Column(String(64), default="general")
    description = Column(String(255), default="")
    updated_by = Column(Integer, ForeignKey("ea_users.id", ondelete="SET NULL"), nullable=True)
    updated_at = Column(DateTime, onupdate=func.now())


class AutomationWorkflow(Base):
    __tablename__ = "ea_automation_workflows"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    trigger_type = Column(String(64), nullable=False)
    trigger_config = Column(JSON, nullable=True)
    actions = Column(JSON, nullable=False)
    is_active = Column(Boolean, default=True)
    last_run_at = Column(DateTime, nullable=True)
    created_by = Column(Integer, ForeignKey("ea_users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())


class WorkflowRun(Base):
    __tablename__ = "ea_workflow_runs"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    workflow_id = Column(Integer, ForeignKey("ea_automation_workflows.id", ondelete="CASCADE"), nullable=False, index=True)
    status_id = Column(SmallInteger, ForeignKey("ea_status_master.id", ondelete="SET NULL"), nullable=True)
    triggered_by = Column(Integer, ForeignKey("ea_users.id", ondelete="SET NULL"), nullable=True)
    input_data = Column(JSON, nullable=True)
    output_data = Column(JSON, nullable=True)
    error_log = Column(Text, nullable=True)
    started_at = Column(DateTime, server_default=func.now())
    completed_at = Column(DateTime, nullable=True)

    workflow = relationship("AutomationWorkflow")


class AuditLog(Base):
    __tablename__ = "ea_audit_logs"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("ea_users.id", ondelete="SET NULL"), nullable=True, index=True)
    action = Column(String(128), nullable=False, index=True)
    entity_type = Column(String(64), nullable=True)
    entity_id = Column(Integer, nullable=True)
    old_values = Column(JSON, nullable=True)
    new_values = Column(JSON, nullable=True)
    ip_address = Column(String(64), default="")
    user_agent = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), index=True)

    user = relationship("User")

    __table_args__ = (
        Index("idx_audit_entity", "entity_type", "entity_id"),
        Index("idx_audit_action_time", "action", "created_at"),
    )


class AuditLogArchive(Base):
    __tablename__ = "ea_audit_logs_archive"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=True, index=True)
    action = Column(String(128), nullable=False)
    entity_type = Column(String(64), nullable=True)
    entity_id = Column(Integer, nullable=True)
    old_values = Column(JSON, nullable=True)
    new_values = Column(JSON, nullable=True)
    ip_address = Column(String(64), default="")
    user_agent = Column(Text, nullable=True)
    archived_at = Column(DateTime, server_default=func.now(), index=True)


class Integration(Base):
    __tablename__ = "ea_integrations"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    provider = Column(String(64), nullable=False)
    config = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True)
    last_sync_at = Column(DateTime, nullable=True)
    created_by = Column(Integer, ForeignKey("ea_users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

