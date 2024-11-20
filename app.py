import uvicorn
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware
from starlette_admin.contrib.sqla import Admin, ModelView

from database import engine
from models import User, Product, Category, Basket, Order
from login import UsernameAndPasswordProvider

app = Starlette()

admin = Admin(engine, title="Example: SQLAlchemy",
              base_url='/',
              auth_provider=UsernameAndPasswordProvider(),
              middlewares=[Middleware(SessionMiddleware, secret_key="qewrerthysclkmsdl")],
              )

admin.add_view(ModelView(User, icon='fas fa-contacts'))
admin.add_view(ModelView(Product, icon='fas fa-products'))
admin.add_view(ModelView(Category, icon='fas fa-products'))
admin.add_view(ModelView(Order, icon='fas fa-products'))
admin.add_view(ModelView(Basket, icon='fas fa-products'))

admin.mount_to(app)
if __name__ == '__main__':
    uvicorn.run(app, host="k.temur.life", port=8016)
