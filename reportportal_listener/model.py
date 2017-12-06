# -*- coding: utf-8 -*-

class Suite(object):
    """Suite object in Report Portal."""

    def __init__(self, attributes):
        """Init suite.

        Args:
            attributes: attr dictionary from robot framework listener.
        """
        super(Suite, self).__init__()
        self.suites = attributes["suites"]
        self.tests = attributes["tests"]
        self.doc = attributes["doc"]
        self.source = attributes["source"]
        self.total_tests = attributes["totaltests"]
        self.longname = attributes["longname"]
        self.robot_id = attributes["id"]
        self.metadata = attributes["metadata"]
        self.status = None
        self.message = None
        self.statistics = None
        if "status" in attributes.keys():
            self.status = attributes["status"]
        if "message" in attributes.keys():
            self.message = attributes["message"]
        if "statistics" in attributes.keys():
            self.statistics = attributes["statistics"]

    def get_type(self):
        """Identify suite type.

        Tests inside - suite is test type in RP.
        No tests inside - suite has suite type in RP.

        Returns:
            str: TEST or SUITE depending object state.
        """
        if self.tests:
            return "TEST"
        else:
            return "SUITE"


class Test(object):
    """Test object in Report Portal."""

    def __init__(self, name=None, attributes=None):
        """Init test.

        Args:
            name: test name.
            attributes: attr dictionary from robot framework listener.
        """
        super(Test, self).__init__()
        self.name = name
        self.critical = attributes["critical"]
        self.template = attributes["template"]
        self.tags = attributes["tags"]
        self.doc = attributes["doc"]
        self.longname = attributes["longname"]
        self.robot_id = attributes["id"]
        self.status = None
        self.message = None
        if "status" in attributes.keys():
            self.status = attributes["status"]
        if "message" in attributes.keys():
            self.message = attributes["message"]


class Keyword(object):
    """Keyword object in Report Portal."""

    def __init__(self, name=None, parent_type=None, attributes=None):
        """Init keyword.

        Args:
            name: keyword name.
            parent_type: link for parent object in the suite hierarchy.
            attributes: attr dictionary from robot framework listener.
        """
        super(Keyword, self).__init__()
        self.name = name
        self.libname = attributes["libname"]
        self.keyword_name = attributes["kwname"]
        self.doc = attributes["doc"]
        self.tags = attributes["tags"]
        self.args = attributes["args"]
        self.assign = attributes["assign"]
        self.keyword_type = attributes["type"]
        self.parent_type = parent_type
        if "status" in attributes.keys():
            self.status = attributes["status"]

    def get_name(self):
        """Get keyword name.

        Returns:
            Наименование, обрезанное до 256 символов.
        """
        assignment = u"{0} = ".format(", ".join(self.assign)) if self.assign else ""
        arguments = u", ".join(self.args)
        full_name = u"{0}{1} ({2})".format(assignment, self.name, arguments)
        return full_name[:256]

    def get_type(self):
        """Get kw type.

        Returns:
            ke type, based on robot framework data.
        """
        if self.keyword_type == "Setup":
            return u"BEFORE_{0}".format(self.parent_type)
        elif self.keyword_type == "Teardown":
            return u"AFTER_{0}".format(self.parent_type)
        else:
            return u"STEP"
