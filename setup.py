from setuptools import setup, find_packages

setup(
    name="bizaxl_core",
    version="1.0.0",
    description="BizAxl Core — Module Manager for Frappe/ERPNext",
    author="BizAxl",
    author_email="dev@bizaxl.com",
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    install_requires=["frappe"],
)
