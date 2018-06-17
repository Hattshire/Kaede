import setuptools
import libkaede
with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name=libkaede.__title__,
    version=libkaede.__version__,
    author=libkaede.__author__,
    author_email=libkaede.__author_email__,
    description=libkaede.__description__,
    long_description=long_description,
    long_description_content_type="text/markdown",
    url=libkaede.__url__,
    packages=setuptools.find_packages(),
    classifiers=(
    	"Development Status :: 1 - Planning",
        "Programming Language :: Python :: 3",
    	"License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: POSIX :: Linux",
        "Environment :: X11 Applications :: GTK",
        "Topic :: Internet",
        "Topic :: Multimedia :: Graphics :: Viewers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
    ),
)
