import numpy as np
import pandas as pd

from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.neighbors import KNeighborsRegressor
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.model_selection import GridSearchCV, train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error
from sklearn.linear_model import LinearRegression, Ridge, Lasso, SGDRegressor


df = pd.read_csv("../data/prepared_data.csv", index_col=0)

ohe_columns = [
    "parking",
    "new_building",
    "apartments",
    "courtyard_view",
    "road_view",
    "district",
    "rooms",
    "joint_wc",
]
scaler_columns = [
    "description_len",
    "general_sq",
    "floor",
    "built",
    "ceil",
    "time_to_underground",
    "all_views",
    "today_views",
    "total_floors",
    "wc_amount",
    "balcony",
    "living_square_ratio",
    "placed_days_ago",
]
preprocessor = ColumnTransformer(
    [
        ("ohe", OneHotEncoder(), ohe_columns),
        (("scaler", StandardScaler(), scaler_columns)),
    ],
    remainder="drop",
)


X = df.drop("price", axis=1)
y = np.log1p(df["price"])

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)
# clf = Pipeline(
#     steps=[("preprocessor", preprocessor), ("classifier", LinearRegression())]
# )
#
# clf.fit(X_train, y_train)
# print("model score: %.3f" % clf.score(X_test, y_test))
# print(mean_absolute_error(y_test, clf.predict(X_test)))
# print(mean_squared_error(y_test, clf.predict(X_test)))
clf_knn = Pipeline(
    steps=[
        ("preprocessor", preprocessor),
        ("regressor", KNeighborsRegressor()),
    ]
)
clf_knn.fit(X_train, y_train)
print()
print("model score: %.3f" % clf_knn.score(X_test, y_test))
print(mean_absolute_error(y_test, clf_knn.predict(X_test)))
print(mean_squared_error(y_test, clf_knn.predict(X_test)))

# grid_ridge_pipeline = Pipeline(
#     steps=[("preprocessor", preprocessor), ("regressor", Ridge()),]
# )
# grid = GridSearchCV(
#     grid_ridge_pipeline,
#     param_grid={
#         "regressor__alpha": np.linspace(2, 3, 10)
#     },
#     cv=5,
# )
#
# grid.fit(X_train, y_train)
# print()
# print("model score: %.3f" % grid.score(X_test, y_test))
# print(mean_absolute_error(grid.predict(X_test), y_test))
# print(mean_squared_error(grid.predict(X_test), y_test))
# print(grid.best_params_)

# grid_knn_pipeline = Pipeline(
#     steps=[("preprocessor", preprocessor), ("regressor", KNeighborsRegressor()),]
# )
# grid_knn = GridSearchCV(
#     grid_knn_pipeline,
#     param_grid={
#         "regressor__n_neighbors": [3,5,10,15,20,30,40,50,60,90,100],
# "regressor__weights": ['uniform', 'distance'],
# "regressor__p": [1,2,3,]
#     },
#     cv=5,
# )
# # {'regressor__n_neighbors': 5, 'regressor__p': 1, 'regressor__weights': 'distance'}
# grid_knn.fit(X_train, y_train)
# print()
# print("model score: %.3f" % grid_knn.score(X_test, y_test))
# print(mean_absolute_error(grid_knn.predict(X_test), y_test))
# print(mean_squared_error(grid_knn.predict(X_test), y_test))
# print(grid_knn.best_params_)


# grid_lasso_pipeline = Pipeline(
#     steps=[("preprocessor", preprocessor), ("regressor", Lasso()),]
# )
# grid_lasso = GridSearchCV(
#     grid_lasso_pipeline,
#     param_grid={
#         "regressor__alpha": [0.01, 0.1, 1, *np.linspace(1, 5, 10)],
#     },
#     cv=5,
# )
# # {'regressor__alpha': 0.01}
# grid_lasso.fit(X_train, y_train)
# print()
# print("model score: %.3f" % grid_lasso.score(X_test, y_test))
# print(mean_absolute_error(grid_lasso.predict(X_test), y_test))
# print(mean_squared_error(grid_lasso.predict(X_test), y_test))
# print(grid_lasso.best_params_)


grid_sgd_pipeline = Pipeline(
    steps=[("preprocessor", preprocessor), ("regressor", SGDRegressor()),]
)
grid_sgd = GridSearchCV(
    grid_sgd_pipeline,
    param_grid={
        "regressor__alpha": [10**-6, 10**-5, 10**-4, 10**-3, 10**-2, 0.1, 1, 1.5, 2, 3],
        "regressor__loss": ['squared_loss', 'huber', 'epsilon_insensitive', 'squared_epsilon_insensitive'],
        "regressor__penalty": ['l1', 'l2',]
    },
    cv=5,
)
grid_sgd.fit(X_train, y_train)
print()
print("model score: %.3f" % grid_sgd.score(X_test, y_test))
print(mean_absolute_error(grid_sgd.predict(X_test), y_test))
print(mean_squared_error(grid_sgd.predict(X_test), y_test))
print(grid_sgd.best_params_)

# {'regressor__alpha': 0.1, 'regressor__loss': 'epsilon_insensitive', 'regressor__penalty': 'l2'}