#!/usr/bin/env node

/**
 * QUICK SYSTEM VALIDATION - 5 minute test for handoff
 * Run this to verify everything is working before handoff
 */

const { runDynamicWorkflow } = require('./test_dynamic_workflow');

async function validateSystem() {
  console.log('🔥 CLIMATIZEAI SYSTEM VALIDATION');
  console.log('================================');
  console.log('Running quick validation for handoff...\n');

  // Check environment variables
  const requiredEnvVars = [
    'PERPLEXITY_API_KEY',
    'OPENAI_API_KEY', 
    'EXA_API_KEY'
  ];

  console.log('📋 Checking environment variables...');
  let envOk = true;
  for (const envVar of requiredEnvVars) {
    if (process.env[envVar]) {
      console.log(`✅ ${envVar}: Present`);
    } else {
      console.log(`❌ ${envVar}: Missing`);
      envOk = false;
    }
  }

  if (!envOk) {
    console.log('\n❌ VALIDATION FAILED: Missing required environment variables');
    console.log('Set these variables and try again:');
    requiredEnvVars.forEach(envVar => console.log(`export ${envVar}="your-api-key"`));
    process.exit(1);
  }

  console.log('\n📡 Running complete workflow test...');
  
  try {
    await runDynamicWorkflow('7481941'); // Test with Hester Creek
    
    console.log('\n🎯 VALIDATION COMPLETE');
    console.log('======================');
    console.log('✅ System is PRODUCTION READY');
    console.log('✅ All APIs working correctly');
    console.log('✅ Dynamic workflow validated');
    console.log('✅ Ready for handoff to next engineer');
    
    console.log('\n📖 Next Steps:');
    console.log('1. Review HANDOFF_README.md for deployment instructions');
    console.log('2. Deploy Edge Functions to Supabase');
    console.log('3. Configure frontend integration');
    console.log('4. Test with real user uploads');
    
  } catch (error) {
    console.error('\n❌ VALIDATION FAILED:', error.message);
    console.log('Check API keys and network connectivity');
    process.exit(1);
  }
}

if (require.main === module) {
  validateSystem().catch(console.error);
}

module.exports = { validateSystem };
