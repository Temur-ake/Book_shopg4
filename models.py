import datetime
from sqlalchemy import Integer, String, Float, JSON, DateTime, ForeignKey, BigInteger
from sqlalchemy.orm import relationship, Mapped, mapped_column, DeclarativeBase

from database import engine


class Base(DeclarativeBase):
    pass


class Order(Base):
    __tablename__ = 'orders'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    courier_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=True)
    date_time: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)
    products: Mapped[dict] = mapped_column(JSON, nullable=True)
    phone_number: Mapped[str] = mapped_column(String, nullable=False)
    order_status: Mapped[str] = mapped_column(String, default='new')
    quantity: Mapped[int] = mapped_column(Integer)

    user = relationship('User', back_populates='orders', foreign_keys=[user_id])
    courier = relationship('User', back_populates='courier_orders', foreign_keys=[courier_id])

    def __repr__(self):
        return (f"<Order(id={self.id}, user_id={self.user_id}, "
                f"courier_id={self.courier_id}, date_time={self.date_time}, "
                f"order_status={self.order_status}, phone_number={self.phone_number})>")


class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String, nullable=False)
    telegram_id: Mapped[str] = mapped_column(String, unique=True, nullable=True)
    phone_number: Mapped[str] = mapped_column(String, nullable=True)
    balance: Mapped[float] = mapped_column(Float, default=0)
    user_type: Mapped[str] = mapped_column(String, default='user')

    orders = relationship('Order', back_populates='user', foreign_keys=[Order.user_id])
    courier_orders = relationship('Order', back_populates='courier', foreign_keys=[Order.courier_id])
    basket_items = relationship('Basket', back_populates='user')

    def __repr__(self):
        return (f"<User(id={self.id}, username={self.username}, "
                f"telegram_id={self.telegram_id}, phone_number={self.phone_number}, "
                f"balance={self.balance}, user_type={self.user_type})>")


class Category(Base):
    __tablename__ = 'categories'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)

    products = relationship('Product', back_populates='category')

    def __repr__(self):
        return (f"<Category(id={self.id}, name={self.name})>")


class Product(Base):
    __tablename__ = 'products'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    description: Mapped[str] = mapped_column(String)
    admin_profit: Mapped[int] = mapped_column(Integer)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    image_url: Mapped[str] = mapped_column(String)
    category_id: Mapped[int] = mapped_column(Integer, ForeignKey('categories.id', ondelete='CASCADE'))

    baskets = relationship('Basket', back_populates='product')
    category = relationship('Category', back_populates='products')

    def __repr__(self):
        return (f"<Product(id={self.id}, name={self.name}, "
                f"quantity={self.quantity}, price={self.price})>")


class Basket(Base):
    __tablename__ = 'baskets'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('users.id', ondelete='CASCADE'))
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey('products.id', ondelete='CASCADE'))
    quantity: Mapped[int] = mapped_column(Integer)

    user = relationship('User', back_populates='basket_items')
    product = relationship('Product', back_populates='baskets')

    def __repr__(self):
        return (f"<Basket(id={self.id}, user_id={self.user_id}, "
                f"product_id={self.product_id}, quantity={self.quantity})>")


Base.metadata.create_all(engine)
