# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from collections import OrderedDict

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.utils.decorators import classonlymethod

from dynamic_forms.formfields import (
    SingleLineTextField, formfield_registry as registry,
)
from dynamic_forms.forms import FormModelForm
from dynamic_forms.models import FormFieldModel, FormModel


class CharField(SingleLineTextField):

    @classonlymethod
    def do_display_data(cls):
        return False


class TestForms(TestCase):

    def test_generate_form_wo_data(self):
        fm = FormModel.objects.create(name='No data', submit_url='/form/')
        form = FormModelForm(model=fm)
        self.assertEqual(form.data, {})

    def test_generate_form_with_data(self):
        fm = FormModel.objects.create(name='With data', submit_url='/form/')
        data = {
            'afield': 'a value',
            'anotherfield': 'another value'
        }
        form = FormModelForm(model=fm, data=data)
        self.assertEqual(form.data, {
            'afield': 'a value',
            'anotherfield': 'another value'
        })

    def test_get_mapped_data(self):
        fm = FormModel.objects.create(name='Form', submit_url='/form/')
        FormFieldModel.objects.create(parent_form=fm, label='Label 1',
            field_type='dynamic_forms.formfields.SingleLineTextField',
            position=3, _options='{"required": false}')
        FormFieldModel.objects.create(parent_form=fm, label='Label 2',
            field_type='dynamic_forms.formfields.SingleLineTextField',
            position=1, _options='{"required": false}')
        FormFieldModel.objects.create(parent_form=fm, label='Label 3',
            field_type='dynamic_forms.formfields.SingleLineTextField',
            position=2, _options='{"required": false}')
        data = {
            'label-1': 'Value 1',
            'label-2': 'Value 2',
        }
        form = FormModelForm(model=fm, data=data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.get_mapped_data(), OrderedDict([
            ('Label 2', 'Value 2',),
            ('Label 3', '',),
            ('Label 1', 'Value 1',),
        ]))
        self.assertEqual(form.get_mapped_data(exclude_missing=True),
            OrderedDict([
                ('Label 2', 'Value 2',),
                ('Label 1', 'Value 1',),
            ])
        )

    def test_get_mapped_data_no_display(self):
        try:
            key = 'tests.test_forms.CharField'
            registry.register(CharField)
            fm = FormModel.objects.create(name='Form', submit_url='/form/')
            FormFieldModel.objects.create(parent_form=fm, label='Label 1',
                field_type='dynamic_forms.formfields.SingleLineTextField',
                position=1)
            FormFieldModel.objects.create(parent_form=fm, label='Label 2',
                field_type=key, position=2)
            data = {
                'label-1': 'Value 1',
                'label-2': 'NOT SHOWN!',
            }
            form = FormModelForm(model=fm, data=data)
            self.assertTrue(form.is_valid())
            self.assertEqual(form.get_mapped_data(), OrderedDict([
                ('Label 1', 'Value 1',),
            ]))
        finally:
            registry.unregister(key)

    def test_multi_select_form_field(self):
        data = {
            'name': 'Some Name',
            'submit_url': '/form/',
            'success_url': '/done/form/',
            'form_template': 'template1.html',
            'success_template': 'template2.html',

            'fields-TOTAL_FORMS': 0,
            'fields-INITIAL_FORMS': 0,
            'fields-MAX_NUM_FORMS': 1000,
            '_save': True,
        }
        self.user = User.objects.create_superuser(username='admin',
            password='password', email='admin@localhost')
        self.client.login(username='admin', password='password')

        response = self.client.post(reverse('admin:dynamic_forms_formmodel_add'), data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<li>This field is required.</li>', count=1, html=True)
