from app import db

class Category(db.Model):
    __tablename__ = 'categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    parent_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
    
    parent = db.relationship('Category', remote_side=[id], backref=db.backref('children', lazy='dynamic'))
    
    def __repr__(self):
        return f'<Category {self.name}>' 

    @classmethod
    def would_create_cycle(cls, category_id, new_parent_id):
        """检查更改父分类是否会创建循环依赖"""
        if category_id == new_parent_id:
            return True
        
        parent = cls.query.get(new_parent_id)
        while parent is not None:
            if parent.id == category_id:
                return True
            parent = parent.parent
        
        return False 