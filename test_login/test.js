const axios = require('axios');
axios.post('http://localhost:3000/api/auth/login', {
  email: 'zhang_yi@gzlab.ac.cn',
  password: 'test_api_123'
}).then(res => console.log('success', res.status))
  .catch(err => console.log('error', err.response?.status, err.response?.data));
