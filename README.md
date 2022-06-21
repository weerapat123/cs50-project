# ShopMi

#### Video Demo: https://youtu.be/5w9iKSELB4k

#### Description:

This project is implemented in **Python** with **MongoDB** as database and **S3 AWS** as image storage.

> **ShopMi** is an e-marketplace where you can buy stuffs or even **sell them**.

It supports cart-shopping feature. You can add your products into a cart. There will be a price summary of all the products and you can check out all products at once.

Unfortunately, I've not implemented the actual payment feature.

There's also a backoffice where you can manage your products you want to sell on ShopMi.
You can add a product yourself with product information. There's also a page that has all the products you've added so far.
If you accidentally remove the product. There's also a history page where you can check which product is added or removed at what time.

[Try now!](https://shopmi.herokuapp.com/)
<br>

![ShopMi logo](./static/shopmi.PNG)

#### Project Detail

Folder **static**

| File                | Description                            |
| ------------------- | -------------------------------------- |
| queries.css         | Contain media query                    |
| specific-styles.css | Contain CSS for specific templates     |
| styles.css          | Contain CSS for common layout template |

Folder **templates**

| File                 | Description                                          |
| -------------------- | ---------------------------------------------------- |
| add_item.html        | Template for add item feature                        |
| apology.html         | Template for when something wrong happens            |
| backoffice.html      | Template for backoffice welcome page                 |
| cart.html            | Template for products summary in cart                |
| change_password.html | Template for password change                         |
| history.html         | Template for product history add/remove log          |
| index.html           | Template for project homepage                        |
| layout.html          | Common template containing header, navbar and footer |
| list_items.html      | Template for list items page                         |
| login.html           | Template for login page                              |
| register.html        | Template for register page                           |

Files

| File             | Description                         |
| ---------------- | ----------------------------------- |
| app.py           | Contain main code of application    |
| aws.py           | Contain aws service                 |
| config.py        | Contain application configuration   |
| helpers.py       | Contain helper functions            |
| Procfile         | Contain commands run by application |
| requirements.txt | Contain dependencies                |

<br>

**Weerapat Treevichien, Thailand**
