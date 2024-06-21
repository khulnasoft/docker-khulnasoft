#! /usr/bin/python
# Copyright 2018-2021 Khulnasoft
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import os
import six
import sys
import uuid
import random
import base64

khulnasoft_ansible_home = os.environ.get('KHULNASOFT_ANSIBLE_HOME')
khulnasoft_ansible_inventory = os.path.join(khulnasoft_ansible_home, "inventory")
sys.path.append(os.path.abspath(khulnasoft_ansible_inventory))

khulnasoft_hec_token = os.environ.get("KHULNASOFT_HEC_TOKEN", None)
khulnasoft_password = os.environ.get("KHULNASOFT_PASSWORD", None)
khulnasoft_idxc_secret = os.environ.get("KHULNASOFT_IDXC_SECRET", None)
khulnasoft_idxc_pass4SymmKey = os.environ.get("KHULNASOFT_IDXC_PASS4SYMMKEY", None)
khulnasoft_shc_secret = os.environ.get("KHULNASOFT_SHC_SECRET", None)
khulnasoft_shc_pass4SymmKey = os.environ.get("KHULNASOFT_SHC_PASS4SYMMKEY", None)

def random_generator(size=24):
    # Use System Random for
    rng = random.SystemRandom()
    b = [chr(rng.randrange(256)) for i in range(size)]
    s = ''.join(b)
    if six.PY2:
        s = base64.b64encode(s)
    else:
        s = base64.b64encode(s.encode()).decode()
    return s


# if there are no environment vars set, lets make some safe defaults
if not khulnasoft_hec_token:
    tempuuid=uuid.uuid4()
    os.environ["KHULNASOFT_HEC_TOKEN"] = str(tempuuid)
if not khulnasoft_password:
    os.environ["KHULNASOFT_PASSWORD"] = random_generator()
if khulnasoft_idxc_pass4SymmKey:
    os.environ["KHULNASOFT_IDXC_PASS4SYMMKEY"] = os.environ["KHULNASOFT_IDXC_SECRET"] = khulnasoft_idxc_pass4SymmKey
elif khulnasoft_idxc_secret:
    os.environ["KHULNASOFT_IDXC_PASS4SYMMKEY"] = os.environ["KHULNASOFT_IDXC_SECRET"] = khulnasoft_idxc_secret
else:
    os.environ["KHULNASOFT_IDXC_PASS4SYMMKEY"] = os.environ["KHULNASOFT_IDXC_SECRET"] = random_generator()
if khulnasoft_shc_secret:
    os.environ["KHULNASOFT_SHC_PASS4SYMMKEY"] = os.environ["KHULNASOFT_SHC_SECRET"] = khulnasoft_shc_pass4SymmKey
elif khulnasoft_shc_pass4SymmKey:
    os.environ["KHULNASOFT_SHC_PASS4SYMMKEY"] = os.environ["KHULNASOFT_SHC_SECRET"] = khulnasoft_shc_secret
else:
    os.environ["KHULNASOFT_SHC_PASS4SYMMKEY"] = os.environ["KHULNASOFT_SHC_SECRET"] = random_generator()
sys.argv.append("--write-to-stdout")
import environ
environ.main()

