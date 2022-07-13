# (C) Datadog, Inc. 2022-present
# All rights reserved
# Licensed under a 3-clause BSD style license (see LICENSE)
BEANS = {
  "jmx_metrics": [
    {
      "include": {
        "attribute": {
          "Count": {
            "metric_type": "gauge", 
            "alias": "foo.bar"
          }
        }, 
        "bean": "my.bean:type=foo,name=baz"
      }
    }, 
    {
      "include": {
        "attribute": {
          "Rate": {
            "metric_type": "gauge", 
            "alias": "foo.bar"
          }
        }, 
        "bean": "my.bean:type=foo,name=baz"
      }
    }
  ]
}
DUPLICATE_BEANS = {
  "jmx_metrics": [
    {
      "include": {
        "attribute": {
          "Count": {
            "metric_type": "gauge", 
            "alias": "foo.bar"
          }
        }, 
        "bean": "my.bean:type=foo,name=baz"
      }
    }, 
    {
      "include": {
        "attribute": {
          "Count": {
            "metric_type": "gauge", 
            "alias": "foo.bar"
          }
        }, 
        "bean": "my.bean:type=foo,name=baz"
      }
    }
  ]
}