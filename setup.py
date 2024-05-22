import setuptools

setuptools.setup(
    name="syscall_handler",
    version="0.0.1",
    url="#",
    author="rkdud007",
    packages=["syscall"],
    package_dir={
        "syscall": "syscall"
    },
    packages=setuptools.find_packages(),
    zip_safe=False,
    package_data={
        "syscall":["*/*.py"],
    }
)
