"""
WPS GetCapabilities request handler
"""
# Author:	Jachym Cepicky
#        	http://les-ejk.cz
#               jachym at les-ejk dot cz
# License:
#
# Web Processing Service implementation
# Copyright (C) 2006 Jachym Cepicky
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA

from Response import Response
from htmltmpl import TemplateError

class GetCapabilities(Response):
    """
    Parses input request obtained via HTTP POST encoding - should be XML
    file.
    """

    def __init__(self,wps):
        """
        Arguments:
           self
           wps   - parent WPS instance
        """
        try:
            Response.__init__(self,wps)
        except Exception, e:
            self.cleanEnv()
            rep = None
            try:
                rep = e.message
            except:
                rep = e.__str__()
            raise self.wps.exceptions.NoApplicableCode(rep)

        try:
            self.template = self.templateManager.prepare(self.templateFile)
        except TemplateError:
            self.cleanEnv()
            raise self.wps.exceptions.InvalidParameterValue("version")

        #
        # ServiceIdentification
        #
        self.templateProcessor.set("encoding",
                                    self.wps.getConfigValue("wps","encoding"))
        self.templateProcessor.set("lang",
                                    self.wps.inputs["language"])
        self.templateProcessor.set("servertitle",
                                    self.wps.getConfigValue("wps","title"))
        self.templateProcessor.set("serverabstract",
                                    self.wps.getConfigValue("wps","abstract"))

        keywordList=[]
        for keyword in self.wps.getConfigValue("wps","keywords").split(','):
            keywordList.append({'keyword':keyword.strip()})
        self.templateProcessor.set("Keywords",keywordList)

        self.templateProcessor.set("Versions",
                                    [{'version':
                                      self.wps.getConfigValue("wps","version")}])
        self.templateProcessor.set("fees",
                                    self.wps.getConfigValue("wps","fees"))
        self.templateProcessor.set("constraints",
                                    self.wps.getConfigValue("wps","constraints"))
        self.templateProcessor.set("url",
                                    self.wps.getConfigValue("wps","serveraddress"))

        #
        # ServiceProvider
        #
        self.templateProcessor.set("providername",
                            self.wps.getConfigValue("provider","providerName"))
        self.templateProcessor.set("individualname",
                        self.wps.getConfigValue("provider","individualName"))
        self.templateProcessor.set("positionname",
                            self.wps.getConfigValue("provider","positionName"))
        self.templateProcessor.set("providersite",
                            self.wps.getConfigValue("provider","providerSite"))
        # phone
        if self.wps.getConfigValue("provider","phoneVoice") or \
        self.wps.getConfigValue("provider","phoneFacsimile"):
            self.templateProcessor.set("phone", 1)
            if self.wps.getConfigValue("provider","phoneVoice"):
                self.templateProcessor.set("phonevoice",
                                    self.wps.getConfigValue("provider","phoneVoice"))
            if self.wps.getConfigValue("provider","phoneFacsimile"):
                self.templateProcessor.set("phonefacsimile",
                                    self.wps.getConfigValue("provider","phoneFacsimile"))
        else:
            self.templateProcessor.set("phone", 0)

        # address
        if self.wps.getConfigValue("provider","deliveryPoint") or \
           self.wps.getConfigValue("provider","city") or \
           self.wps.getConfigValue("provider","administrativeArea") or \
           self.wps.getConfigValue("provider","postalCode") or \
           self.wps.getConfigValue("provider","country") or \
           self.wps.getConfigValue("provider","electronicMailAddress"):

            self.templateProcessor.set("address", 1)
            if self.wps.getConfigValue("provider","deliveryPoint"):
                self.templateProcessor.set("deliverypoint",
                            self.wps.getConfigValue("provider","deliveryPoint"))
            if self.wps.getConfigValue("provider","city"):
                self.templateProcessor.set("city",
                            self.wps.getConfigValue("provider","city"))
            if self.wps.getConfigValue("provider","administrativeArea"):
                self.templateProcessor.set("administrativearea",
                        self.wps.getConfigValue("provider","administrativeArea"))
            if self.wps.getConfigValue("provider","postalCode"):
                self.templateProcessor.set("postalcode",
                            self.wps.getConfigValue("provider","postalCode"))
            if self.wps.getConfigValue("provider","country"):
                self.templateProcessor.set("country",
                            self.wps.getConfigValue("provider","country"))
            if self.wps.getConfigValue("provider","electronicMailAddress"):
                self.templateProcessor.set("electronicmailaddress",
                    self.wps.getConfigValue("provider","electronicMailAddress"))
        else:
           self.templateProcessor.set("address", 0)

        # OperationsMetadata
        self.templateProcessor.set("Operations",
             [{"operation":"GetCapabilities",
               "url":self.wps.getConfigValue("wps","serveraddress")},
              {"operation":"DescribeProcess",
               "url":self.wps.getConfigValue("wps","serveraddress")},
              {"operation":"Execute",
               "url":self.wps.getConfigValue("wps","serveraddress")}])

        # Processes
        processesData = []

        # Import processes

        for processName in self.processes.__all__:

            processData = {}
            try:
                # dynamic module import from processes dir:
                module = __import__(self.processes.__name__, globals(),\
                                    locals(), [processName])
                process = eval("module."+processName+".Process()")

                # process identifier must be == package name
                if process.identifier != processName:
                    raise ImportError(
                            "Process identifier \"%s\" != package name \"%s\": File name has to be the same, as the identifier is!" %\
                            (process.identifier, processName))
                # set selected language
                process.lang.setCode(self.wps.inputs["language"])

                processData["processok"] = 1
                processData["identifier"] = process.identifier
                processData["processversion"] = process.version
                processData["title"] = process.i18n(process.title)
                if process.abstract:
                    processData["abstract"] = process.i18n(process.abstract)
                if process.metadata:
                    metadata=[]
                    for meta in process.metadata:
                        metadata.append({"metadatatitle":meta})
                    processData["Metadata"] = metadata
                if process.profile:
                    profiles=[]
                    for profile in process.profile:
                        profiles.append({"profile":profile})
                    processData["Profiles"] = profiles
                if process.wsdl:
                    processData["wsdl"] = process.wsdl

            except Exception, e:
                processData["processok"] = 0
                processData["process"] = processName
                processData["exception"] = e
            processesData.append(processData)
        self.templateProcessor.set("Processes",processesData)



        # Language
        self.templateProcessor.set("defaultlanguage", self.wps.defaultLanguage)
        languages = []
        for lang in self.wps.languages:
            languages.append({"language":lang})
        self.templateProcessor.set("Languages",languages)

        self.response = self.templateProcessor.process(self.template)
        return
