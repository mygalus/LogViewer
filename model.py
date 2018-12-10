import os


class Model:
    def __init__(self):
        '''
        Initializes the two members the class holds:
        the file name and its contents.
        '''
        self.directoryName = None
        self.fileName = None
        self.fileContent = ""
        # and not 1000000 as 1024 * 1024
        self.sizeMaxToOpen = 1024*1024*1024*4 # 400mb

    def isValid(self, fileName):
        '''
        returns True if the file exists and can be
        opened.  Returns False otherwise.
        '''
        try:
            file = open(fileName, 'r')
            file.close()
            return True
        except:
            return False

    def setDirectoryName(self, directoryName):
        '''
        sets the member fileName to the value of the argument
        if the file exists.  Otherwise resets both the filename
        and file contents members.
        '''
        self.directoryName = directoryName

    def getDirectoryName(self):
        '''
        Returns the name of the file name member.
        '''
        return self.directoryName

    def setFileName(self, fileName):
        '''
        sets the member fileName to the value of the argument
        if the file exists.  Otherwise resets both the filename
        and file contents members.
        '''
        statinfo = os.stat(fileName)
        if statinfo.st_size >= self.sizeMaxToOpen:
            self.fileName = fileName
            self.fileContents = "File is bigger than the limit configured in the tools"
        else:
            if self.isValid(fileName):
                self.fileName = fileName
                try:
                    self.fileContents = open(fileName, 'r').read()
                except:
                    self.fileContents = "File not valid to open"
            else:
                self.fileContents = ""
                self.fileName = ""

    def getFileName(self):
        '''
        Returns the name of the file name member.
        '''
        return self.fileName

    def getFileContents(self):
        '''
        Returns the contents of the file if it exists, otherwise
        returns an empty string.
        '''
        return self.fileContents

    def writeDoc(self, text):
        '''
        Writes the string that is passed as argument to a
        a text file with name equal to the name of the file
        that was read, plus the suffix ".bak"
        '''
        if self.isValid(self.fileName):
            fileName = self.fileName + ".bak"
            file = open(fileName, 'w')
            file.write(text)
            file.close()