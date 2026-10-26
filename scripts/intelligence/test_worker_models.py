import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'skills/neptune/scripts'))
import worker_models as policy


def catalogue():
    return [{'slug': name, 'visibility': 'list',
             'supported_reasoning_levels': [{'effort': e} for e in ['low','medium','high','xhigh','max','ultra']]}
            for name in ['gpt-6-luna','gpt-5.6-luna','gpt-6-sol','gpt-5.6-terra','gpt-5.6-sol','gpt-6.1-sol','gpt-6-astra']]


class WorkerModelTests(unittest.TestCase):
    def pick(self, **args):
        return policy.choose(catalogue=catalogue(), scope={'task':'fixture'}, **args)

    def test_task_characteristics_not_task_titles_drive_settings(self):
        for kind, model, effort in [('simple','gpt-6-luna','low'), ('bounded','gpt-6-luna','medium'),
                                     ('complex','gpt-6-luna','high'), ('sensitive','gpt-6-sol','high')]:
            with self.subTest(kind=kind):
                got=self.pick(complexity=kind)
                self.assertEqual((got['model'],got['effort']),(model,effort))
                self.assertFalse(got['approval_required'])

    def test_all_nonrestricted_catalogued_models_and_efforts_can_be_justified(self):
        for model in ['gpt-6-luna','gpt-5.6-luna','gpt-6-sol','gpt-5.6-terra','gpt-5.6-sol']:
            for effort in ['low','medium','high','xhigh','max','ultra']:
                self.assertFalse(self.pick(model=model,effort=effort,reason='Concrete task evidence')['approval_required'])

    def test_only_two_models_require_task_specific_approval(self):
        for model in policy.APPROVAL_MODELS:
            got=self.pick(model=model,effort='medium',reason='Task requires stronger model')
            self.assertTrue(got['approval_required'])
            approval={**got['approval_request'],'user_reference':'Human approved fixture task'}
            self.assertFalse(self.pick(model=model,effort='medium',reason='Task requires stronger model',approval=approval)['approval_required'])
            changed=policy.choose(model=model,effort='medium',reason='Task requires stronger model',
                scope={'task':'different'},approval=approval,catalogue=catalogue())
            self.assertTrue(changed['approval_required'])

    def test_effort_change_or_missing_reference_invalidates_approval(self):
        got=self.pick(model='gpt-6.1-sol',effort='medium',reason='Evidence')
        approval={**got['approval_request'],'user_reference':'Human approval'}
        self.assertTrue(self.pick(model='gpt-6.1-sol',effort='high',reason='Evidence',approval=approval)['approval_required'])
        approval['user_reference']=''
        self.assertTrue(self.pick(model='gpt-6.1-sol',effort='medium',reason='Evidence',approval=approval)['approval_required'])

    def test_repeat_failures_raise_effort_then_request_upgrade(self):
        self.assertEqual(self.pick(attempts=1)['effort'],'high')
        self.assertEqual(self.pick(complexity='complex',attempts=1)['model'],'gpt-6-sol')
        self.assertTrue(self.pick(attempts=2)['approval_required'])
        with self.assertRaises(ValueError): self.pick(attempts=2,model='gpt-6-luna',reason='Retry again')

    def test_missing_hidden_and_unsupported_models_or_efforts_fail_closed(self):
        with self.assertRaises(ValueError): self.pick(model='made-up-model',reason='Evidence')
        with self.assertRaises(ValueError): self.pick(effort='nonexistent',reason='Evidence')
        with self.assertRaises(ValueError): self.pick(model='gpt-6-sol')
        hidden=[{**catalogue()[0],'visibility':'hide'}]
        with self.assertRaises(ValueError): policy.choose(catalogue=hidden)
        with self.assertRaises(ValueError): policy.choose(catalogue=[])
        with self.assertRaises(ValueError): self.pick(attempts=3)


if __name__=='__main__': unittest.main()
