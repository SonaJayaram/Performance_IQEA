from sqlalchemy import Column, Integer, String, Text, DateTime, func, LargeBinary
from datetime import datetime
from utilities.db_utils.base import Base  # Shared Base


class Prompt(Base):
    __tablename__ = "prompts"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    prompt_name = Column(String(255), nullable=False, unique=True)
    prompt_text = Column(Text, nullable=False)  # Supports long prompt text
    description = Column(Text, nullable=True)   # Optional: describe prompt purpose

    created_on = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(100), nullable=True)

    updated_on = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(String(100), nullable=True)

    def __repr__(self):
        return f"<Prompt(name='{self.prompt_name}', created_by='{self.created_by}')>"

class Action(Base):
    __tablename__ = 'actions'
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True)
    action_name = Column(Text, nullable=False)  # this is the file name
    file_data = Column(LargeBinary, nullable=False)
    created_by = Column(Text, nullable=False)
    created_on = Column(DateTime, server_default=func.now())

class Pagefile(Base):
    __tablename__ = 'pagefile'
    __table_args__ = {"extend_existing": True}
    id = Column(Integer, primary_key=True)
    pagefile_name = Column(Text, nullable=False)  # this is the file name
    file_data = Column(LargeBinary, nullable=False)
    created_by = Column(Text, nullable=False)
    created_on = Column(DateTime, server_default=func.now())

class Testcasefile(Base):
    __tablename__ = 'testcase'
    __table_args__ = {"extend_existing": True}
    id = Column(Integer, primary_key=True)
    testcase_name = Column(Text, nullable=False)  # this is the file name
    file_data = Column(LargeBinary, nullable=False)
    created_by = Column(Text, nullable=False)
    created_on = Column(DateTime, server_default=func.now())

class Testfile(Base):
    __tablename__ = 'testfile'
    __table_args__ = {"extend_existing": True}
    id = Column(Integer, primary_key=True)
    testfile_name = Column(Text, nullable=False)  # this is the file name
    file_data = Column(LargeBinary, nullable=False)
    created_by = Column(Text, nullable=False)
    created_on = Column(DateTime, server_default=func.now())

class Fetaurefile(Base):
    __tablename__ = 'featurefile'
    __table_args__ = {"extend_existing": True}
    id = Column(Integer, primary_key=True)
    featurefile_name = Column(Text, nullable=False)  # this is the file name
    file_data = Column(LargeBinary, nullable=False)
    created_by = Column(Text, nullable=False)
    created_on = Column(DateTime, server_default=func.now())

class Screenshot(Base):
    __tablename__ = 'screenshot'
    __table_args__ = {"extend_existing": True}
    id = Column(Integer, primary_key=True)
    page_name = Column(Text, nullable=False)
    url = Column(Text, nullable=False)
    image_data = Column(LargeBinary, nullable=False)
    created_on = Column(DateTime, server_default=func.now())
    created_by = Column(Text, nullable=False)  # optional