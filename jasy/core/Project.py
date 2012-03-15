#
# Jasy - Web Tooling Framework
# Copyright 2010-2012 Zynga Inc.
#

import os, logging, json

from jasy.core.Item import Item
from jasy.js.Package import Package
from jasy.js.Class import Class

from jasy.core.Cache import Cache
from jasy.core.Error import *
from jasy.core.Markdown import *

__all__ = ["Project", "getProject"]


extensions = {
    # Image Assets
    ".jpg" : "assets",
    ".jpeg" : "assets",
    ".png" : "assets",
    ".gif" : "assets",
    ".svg" : "assets",
    ".ico" : "assets",
    
    # Date Assets
    ".json" : "assets",
    ".html" : "assets",
    ".txt" : "assets",
    
    # Font Assets
    ".eot" : "assets",
    ".ttf" : "assets",
    ".woff" : "assets",
    
    # Style Assets
    ".css" : "assets",

    # Meta Assets
    ".manifest" : "assets",

    # Processed Items
    ".js" : "classes",
    ".sass" : "styles",
    ".scss" : "styles",
    ".less" : "styles",
    ".tmpl" : "templates",
    ".po": "translations"
}



def getKey(data, key, default=None):
    if key in data:
        return data[key]
    else:
        return default


projects = {}

def getProject(path, config=None):
    if not path in projects:
        projects[path] = Project(path, config)

    return projects[path]


class Project():
    
    def __init__(self, path, config=None):
        """
        Constructor call of the project. 

        - First param is the path of the project relative to the current working directory.
        - Config can be read from jasyproject.json or using constructor parameter @config
        - Parent is used for structural debug messages (dependency trees)
        """
        
        if not os.path.isdir(path):
            raise JasyError("Invalid project path: %s (absolute: %s)" % (path, os.path.abspath(path)))
        
        # Only store and work with full path
        self.__path = os.path.abspath(path)
        
        # Intialize item registries
        self.classes = {}
        self.styles = {}
        self.templates = {}
        self.translations = {}
        self.assets = {}        

        # Load project configuration
        configFilePath = os.path.join(self.__path, "jasyproject.json")
        isJasyProject = os.path.exists(configFilePath)
        if isJasyProject:
            try:
                storedConfig = json.load(open(configFilePath))
            except ValueError as err:
                raise JasyError("Could not parse jasyproject.json at %s: %s" % (configFile, err))
                
            if config:
                for key in storedConfig:
                    if not key in config:
                        config[key] = storedConfig[key]
            else:
                config = storedConfig
            
        # Initialize cache
        try:
            self.__cache = Cache(self.__path)
        except IOError as err:
            raise JasyError("Could not initialize project. Cache file could not be initialized! %s" % err)
        
        # Read name from manifest or use the basename of the project's path
        self.__name = getKey(config, "name", os.path.basename(self.__path))
            
        # Read requires
        self.__requires = getKey(config, "requires", {})
        
        # Defined whenever no package is defined and classes/assets are not stored in the toplevel structure.
        self.__package = getKey(config, "package", self.__name if isJasyProject else None)

        # Read fields (for injecting data into the project and build permuations)
        self.__fields = getKey(config, "fields", {})

        logging.info("- Initializing project: %s (from: %s)", self.__name, self.__path)
            
        # Processing custom content section. Only supports classes and assets.
        if "content" in config:
            self.addContent(config["content"])

        # This section is a must for non jasy projects
        elif not isJasyProject:
            raise JasyError("Missing 'content' section for compat project!")

        # Application projects
        elif self.hasDir("source"):
            if self.hasDir("source/class"):
                self.addDir("source/class", self.classes)

            if self.hasDir("source/asset"):
                self.addDir("source/asset", self.assets)
            
            if self.hasDir("source/style"):
                self.addDir("source/style", self.styles)

            if self.hasDir("source/template"):
                self.addDir("source/template", self.templates)

            if self.hasDir("source/translation"):
                self.addDir("source/translation", self.translations)

        # Simple projects
        elif self.hasDir("src"):
            self.addDir("src")
        elif self.hasDir("class"):
            self.addDir("class", self.classes)
        elif self.hasDir("style"):
            self.addDir("style", self.styles)
        elif self.hasDir("asset"):
            self.addDir("asset", self.assets)

        # Generate summary
        summary = []
        for section in ["classes", "assets", "styles", "translations", "templates"]:
            content = getattr(self, section, None)
            if content:
                summary.append("%s %s" % (len(content), section))

        if summary:
            logging.info("  - Found: %s", ", ".join(summary))
        else:
            logging.info("  - Empty project?!?")



    #
    # FILE SYSTEM INDEXER
    #
    
    def hasDir(self, directory):
        full = os.path.join(self.__path, directory)
        if os.path.exists(full):
            if not os.path.isdir(full):
                raise JasyError("Expecting %s to be a directory: %s" % full)
            
            return True
        
        return False
        
        
    def shouldIgnoreFile(self, fileName):
        """ Exclude dotted hidden files and specific file names. """
        return fileName[0] == "." or fileName in ("jasyproject.json", "package.json", "index.html", "index.css", "index.js")
        
        
    def addContent(self, content):
        for fileId in content:
            fileContent = content[fileId]
            if len(fileContent) == 0:
                raise JasyError("Empty content!")

            fileExtension = os.path.splitext(fileContent[0])[1]
            if len(fileContent) == 1:
                filePath = os.path.join(self.__path, fileContent[0])
            else:
                filePath = [os.path.join(self.__path, filePart) for filePart in fileContent]
            
            if fileExtension == ".js":
                if fileId in self.classes:
                    raise JasyError("Class ID was registered before: %s" % fileId)
                else:
                    self.classes[fileId] = Class(self, fileId).attach(filePath)
                    
            elif fileExtension in extensions and extensions[fileExtension] == "assets":
                if fileId in self.assets:
                    raise JasyError("Item ID was registered before: %s" % fileId)
                else:
                    self.assets[fileId] = Item(self, fileId).attach(filePath)
                    
            else:
                raise JasyError("Invalid file content: %s" % fileId)
        
        
        
    def addDir(self, directory, acceptDist=None):
        
        path = os.path.join(self.__path, directory)
        if not os.path.exists(path):
            return

        for dirPath, dirNames, fileNames in os.walk(path):
            for dirName in dirNames:
                # Filter dotted directories like .git, .bzr, .hg, .svn, etc.
                if dirName.startswith("."):
                    dirNames.remove(dirName)

                # Filter sub projects
                if os.path.exists(os.path.join(dirPath, dirName, "jasyproject.json")):
                    dirNames.remove(dirName)
                    
                # Remove unit tests (expecting test as fixed name, pretty much a convention)
                if dirName == "test":
                    dirNames.remove(dirName)

            relDirPath = os.path.relpath(dirPath, path)

            for fileName in fileNames:
                if not self.shouldIgnoreFile(fileName):
                    relPath = os.path.normpath(os.path.join(relDirPath, fileName))
                    fullPath = os.path.join(dirPath, fileName)
                    fileExtension = os.path.splitext(fileName)[1]

                    # Generating file ID from relative path
                    if fileName == "package.md":
                        fileId = os.path.dirname(relPath)
                    elif fileExtension in (".js", ".tmpl", ".po"):
                        fileId = os.path.splitext(relPath)[0]
                    else:
                        fileId = relPath

                    # Prepand package
                    if self.__package:
                        fileId = "%s/%s" % (self.__package, fileId)

                    # Replace slash by "dot" for classes
                    if fileExtension == ".js" or fileName == "package.md":
                        fileId = fileId.replace(os.sep, ".")

                    # Special named package.md files are used as package docs
                    if fileName == "package.md" or fileExtension == ".js":
                        item = Class(self, fileId).attach(fullPath)
                        distname = "classes"
                    else:
                        item = Item(self, fileId).attach(fullPath)
                        if fileExtension in extensions:
                            distname = extensions[fileExtension]
                        else:
                            logging.debug("Ignoring unsupported file extension: %s in %s", fileExtension, relPath)
                            return

                    # Get storage dict
                    dist = getattr(self, distname)

                    if acceptDist and dist != acceptDist:
                        logging.warn("Could not add %s from %s", fileId, directory)
                        return

                    if fileId in dist:
                        raise JasyError("Item ID was registered before: %s" % fileId)

                    # logging.info("  - Registering %s %s" % (item.kind, fileId))
                    dist[fileId] = item



    #
    # ESSENTIALS
    #
    
    def __str__(self):
        return self.__path

    def __repr__(self):
        return self.__path
    

    def getRequires(self):
        """
        Return the project requirements as project instances
        """

        result = []
        for entry in self.__requires:
            if type(entry) is dict:
                source = entry["source"]
                config = entry["config"]
            else:
                source = entry
                config = None
                
            path = os.path.normpath(os.path.join(self.__path, source))
            result.append(getProject(path, config))
            
        return result


    def getFields(self):
        """ Return the project defined fields which may be configured by the build script """
        return self.__fields


    def getClassByName(self, className):
        """ Finds a class by its name."""

        try:
            return self.getClasses()[className]
        except KeyError:
            return None

    def getName(self):
        return self.__name
    
    def getPath(self):
        return self.__path
    
    def getPackage(self):
        return self.__package



    #
    # CACHE API
    #
    
    def getCache(self):
        return self.__cache
    
    def clearCache(self):
        self.__cache.clear()
        
    def close(self):
        self.__cache.close()



    #
    # LIST ACCESSORS
    #

    def getClasses(self):
        """ Returns all project JavaScript classes. Requires all files to have a "js" extension. """
        return self.classes

    def getAssets(self):
        """ Returns all project asssets (images, stylesheets, static data, etc.). """
        return self.assets

    def getStyles(self):
        """ Returns all styles which pre-processor needs. Lists all Sass, Scss, Less files. """
        return self.styles
        
    def getTemplates(self):
        """ Returns all templates files. Supports Hogan.js/Mustache files with .tmpl extension. """
        return self.templates

    def getTranslations(self):
        """ Returns all translation files. Supports gettext style PO files with .po extension. """
        return self.translations

        