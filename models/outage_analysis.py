# coding: utf-8

from __future__ import absolute_import
from datetime import date, datetime  # noqa: F401

from typing import List, Dict  # noqa: F401

from models.base_model_ import Model
import util


class OutageAnalysis(Model):
    """NOTE: This class is auto generated by OpenAPI Generator
    (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(self, name=None, type=None, modelid=None, nm1_list=None, nm2_list=None, param=None):  # noqa: E501
        """OutageAnalysis - a model defined in OpenAPI

        :param name: The name of this OutageAnalysis.  # noqa: E501
        :type name: str
        :param type: The type of this OutageAnalysis.  # noqa: E501
        :type type: str
        :param modelid: The modelid of this OutageAnalysis.  # noqa: E501
        :type modelid: int
        :param nm1_list: The nm1_list of this OutageAnalysis.  # noqa: E501
        :type nm1_list: List[str]
        :param nm2_list: The nm2_list of this OutageAnalysis.  # noqa: E501
        :type nm2_list: List[str]
        :param param: The param of this OutageAnalysis.  # noqa: E501
        :type param: Dict[str, AnyType]
        """
        self.openapi_types = {
            'name': str,
            'type': str,
            'modelid': int,
            'nm1_list': List[str],
            'nm2_list': List[str],
            'param': Dict[str, {}]
        }

        self.attribute_map = {
            'name': 'name',
            'type': 'type',
            'modelid': 'modelid',
            'nm1_list': 'nm1List',
            'nm2_list': 'nm2List',
            'param': 'param'
        }

        self._name = name
        self._type = type
        self._modelid = modelid
        self._nm1_list = nm1_list
        self._nm2_list = nm2_list
        self._param = param

    @classmethod
    def from_dict(cls, dikt) -> 'OutageAnalysis':
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The OutageAnalysis of this OutageAnalysis.  # noqa: E501
        :rtype: OutageAnalysis
        """
        return util.deserialize_model(dikt, cls)

    @property
    def name(self):
        """Gets the name of this OutageAnalysis.

        Name of analysis case  # noqa: E501

        :return: The name of this OutageAnalysis.
        :rtype: str
        """
        return self._name

    @name.setter
    def name(self, name):
        """Sets the name of this OutageAnalysis.

        Name of analysis case  # noqa: E501

        :param name: The name of this OutageAnalysis.
        :type name: str
        """
        if name is None:
            raise ValueError("Invalid value for `name`, must not be `None`")  # noqa: E501

        self._name = name

    @property
    def type(self):
        """Gets the type of this OutageAnalysis.

        Type of analysis, e.g. PowerflowAnalysis  # noqa: E501

        :return: The type of this OutageAnalysis.
        :rtype: str
        """
        return self._type

    @type.setter
    def type(self, type):
        """Sets the type of this OutageAnalysis.

        Type of analysis, e.g. PowerflowAnalysis  # noqa: E501

        :param type: The type of this OutageAnalysis.
        :type type: str
        """
        if type is None:
            raise ValueError("Invalid value for `type`, must not be `None`")  # noqa: E501

        self._type = type

    @property
    def modelid(self):
        """Gets the modelid of this OutageAnalysis.

        Model to consider for analysis  # noqa: E501

        :return: The modelid of this OutageAnalysis.
        :rtype: int
        """
        return self._modelid

    @modelid.setter
    def modelid(self, modelid):
        """Sets the modelid of this OutageAnalysis.

        Model to consider for analysis  # noqa: E501

        :param modelid: The modelid of this OutageAnalysis.
        :type modelid: int
        """
        if modelid is None:
            raise ValueError("Invalid value for `modelid`, must not be `None`")  # noqa: E501

        self._modelid = modelid

    @property
    def nm1_list(self):
        """Gets the nm1_list of this OutageAnalysis.

        List of N-1 components  # noqa: E501

        :return: The nm1_list of this OutageAnalysis.
        :rtype: List[str]
        """
        return self._nm1_list

    @nm1_list.setter
    def nm1_list(self, nm1_list):
        """Sets the nm1_list of this OutageAnalysis.

        List of N-1 components  # noqa: E501

        :param nm1_list: The nm1_list of this OutageAnalysis.
        :type nm1_list: List[str]
        """
        if nm1_list is None:
            raise ValueError("Invalid value for `nm1_list`, must not be `None`")  # noqa: E501

        self._nm1_list = nm1_list

    @property
    def nm2_list(self):
        """Gets the nm2_list of this OutageAnalysis.

        List of N-2 components  # noqa: E501

        :return: The nm2_list of this OutageAnalysis.
        :rtype: List[str]
        """
        return self._nm2_list

    @nm2_list.setter
    def nm2_list(self, nm2_list):
        """Sets the nm2_list of this OutageAnalysis.

        List of N-2 components  # noqa: E501

        :param nm2_list: The nm2_list of this OutageAnalysis.
        :type nm2_list: List[str]
        """

        self._nm2_list = nm2_list

    @property
    def param(self):
        """Gets the param of this OutageAnalysis.

        attribute map, e.g. strings and numbers  # noqa: E501

        :return: The param of this OutageAnalysis.
        :rtype: Dict[str, AnyType]
        """
        return self._param

    @param.setter
    def param(self, param):
        """Sets the param of this OutageAnalysis.

        attribute map, e.g. strings and numbers  # noqa: E501

        :param param: The param of this OutageAnalysis.
        :type param: Dict[str, AnyType]
        """

        self._param = param
