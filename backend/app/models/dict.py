"""字典模型（沿用 ALMD sys_dict_type / sys_dict_data 模式）"""
from datetime import datetime
from sqlalchemy import BigInteger, String, Integer, SmallInteger, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


class SysDictType(Base):
    """字典类型表"""
    __tablename__ = "sys_dict_type"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    dict_name: Mapped[str] = mapped_column(String(128), nullable=False, comment="字典名称")
    dict_code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, comment="字典编码(唯一)")
    description: Mapped[str] = mapped_column(String(256), default="", comment="字典描述")
    sort_order: Mapped[int] = mapped_column(Integer, default=0, comment="排序号")
    status: Mapped[int] = mapped_column(SmallInteger, default=1, comment="状态: 0=禁用,1=正常")
    is_deleted: Mapped[int] = mapped_column(SmallInteger, default=0, comment="逻辑删除")
    created_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    updated_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)

    # 关联字典数据
    datas: Mapped[list["SysDictData"]] = relationship(
        back_populates="dict_type",
        lazy="selectin",
        cascade="all, delete-orphan",
    )


class SysDictData(Base):
    """字典数据/码值表"""
    __tablename__ = "sys_dict_data"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    dict_type_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("sys_dict_type.id"), nullable=False)
    dict_label: Mapped[str] = mapped_column(String(128), nullable=False, comment="字典标签(显示值)")
    dict_value: Mapped[str] = mapped_column(String(128), nullable=False, comment="字典键值(存储值)")
    dict_key: Mapped[str] = mapped_column(String(64), nullable=False, comment="字典键名")
    css_class: Mapped[str] = mapped_column(String(64), default="")
    list_class: Mapped[str] = mapped_column(String(64), default="", comment="列表样式类")
    description: Mapped[str] = mapped_column(String(255), default="", comment="字典项说明")
    is_default: Mapped[int] = mapped_column(SmallInteger, default=0, comment="是否默认")
    sort_order: Mapped[int] = mapped_column(Integer, default=0, comment="排序号")
    status: Mapped[int] = mapped_column(SmallInteger, default=1, comment="状态")
    is_deleted: Mapped[int] = mapped_column(SmallInteger, default=0)
    created_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    updated_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)

    dict_type: Mapped["SysDictType"] = relationship(back_populates="datas")

    __table_args__ = (
        UniqueConstraint("dict_type_id", "dict_key", name="uk_dict_type_key"),
    )